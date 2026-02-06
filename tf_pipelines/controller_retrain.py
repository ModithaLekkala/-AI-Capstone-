from threading import Thread, Event, Lock
from scapy.all import sniff, sendp, Ether, raw, bind_layers
from helpers.pycommon import (BNNFeaturesHeader, BNNDense, BNNTiny, BNNWide,
                              DUMMY_ETHER_SRC, DUMMY_ETHER_DST,
                              BNN_TYPE_ETHER, FEATURES_TYPE_ETHER, nn,
                              CONCURRENT_ACTIVE_FLOWS)
from helpers.mlp import MLP
from helpers.bfrt_bnn import BNNPipeline
from helpers.utils import hex_lists_to_ints, none_or_str, load_dataset, get_cfg
from ml_helpers.simple_trainer import SimpleTrainer
from ml_helpers.utils import analyze_confidence_distribution
from sklearn.model_selection import train_test_split
import argparse
import sys
import os
import json
import time
import numpy as np
import torch

np.random.seed(42)
torch.manual_seed(42)

EXPERIMENT_NAME = 'DS_RETRAINING'

FEATURE_EXTRACTOR_CPU_INTF = 'veth5'
BNN_TO_CPU_INTF = 'veth7'
CPU_TO_BNN_INTF = 'veth8'

ARCH_MAP = {
    'dense': ('binocular_dense', BNNDense),
    'tiny':  ('binocular_tiny',  BNNTiny),
    'wide':  ('binocular_wide',  BNNWide),
}

args = None
bfrt_bnn = None
BNN = None

# ML state (set in initial_training_pipeline)
teacher = None
student = None
shap_feat_idx = None
confident_score_array = None
current_l1_w = None
current_l2_w = None
X_train_full = None
Y_train_full = None
X_val_full = None
Y_val_full = None
RES_DIR = None

# Experiment config (set in main)
CRITICAL_RETRAIN_SAMPLES = None
OG_RETRAIN_SAMPLES = None
RETRAINING_EPOCHS = None

# Online critical sample collection
stored_features = {}
critical_samples_X = []
critical_samples_Y = []
retraining_lock = Lock()
retraining_triggered = False
alert_count = 0
uncertain_count = 0

bind_layers(Ether, BNNFeaturesHeader, type=FEATURES_TYPE_ETHER)


# ---------------------------------------------------------------------------
#  Utilities
# ---------------------------------------------------------------------------

def bits_to_numpy(bit_string):
    """Convert a binary string (e.g. '01101...') to a float32 numpy array."""
    return np.array([int(b) for b in bit_string], dtype=np.float32)


# ---------------------------------------------------------------------------
#  Packet processing
# ---------------------------------------------------------------------------

def process_cpu_packet(pkt):
    """Handle a packet from the feature extractor: store features + trigger BNN."""
    global args, bfrt_bnn, stored_features

    try:
        packet = Ether(raw(pkt))
        if packet.type != FEATURES_TYPE_ETHER:
            return

        print('\nPacket received from feature extractor pipeline:')
        cpu_header = packet[BNNFeaturesHeader]
        print(cpu_header.summary())

        # Store full 168-bit feature vector for later retrieval
        full_bits = cpu_header.bits_concat_126b()
        full_features = bits_to_numpy(full_bits)

        bnn_input = cpu_header.to_hex()
        print('Load features into BNN input registers:')

        if args.arch == 'wide':
            bnn_input = bnn_input[:32]
            bnn_input = '{:0128b}'.format(int(bnn_input, 16))
        elif args.arch == 'dense':
            bnn_input = bnn_input[:33]
            bnn_input = '{:0140b}'.format(int(bnn_input, 16))
        elif args.arch == 'tiny':
            bnn_input = bnn_input[:25]
            bnn_input = '{:098b}'.format(int(bnn_input, 16))

        loaded_offset = bfrt_bnn.load_bnn_input_reg(bnn_input)

        # Store features keyed by offset for BNN response handler
        stored_features[loaded_offset] = full_features

        trigger = Ether(src=DUMMY_ETHER_SRC, dst=DUMMY_ETHER_DST,
                        type=BNN_TYPE_ETHER) / BNN(
                            input_offset=loaded_offset,
                            input_offset_cp=loaded_offset)
        print('Send trigger packet to BNN pipeline.')
        sendp(trigger, iface=CPU_TO_BNN_INTF, verbose=False)

    except AssertionError as e:
        print(f"[CPU->BNN] Input error: {e}")
    except Exception as e:
        print(f"[CPU->BNN] Unexpected processing error: {e}")


def handle_bnn_response(resp):
    """Handle BNN response: log results, collect critical samples if uncertain."""
    global args, bfrt_bnn, teacher, current_l1_w, current_l2_w
    global critical_samples_X, critical_samples_Y, stored_features
    global retraining_triggered, alert_count, uncertain_count

    try:
        if not resp:
            print("no reply")
            return

        ether = Ether(raw(resp))
        if BNN not in ether:
            return

        def handle_conf_score(iter_l0out):
            print('Compose l0_out from parts:', iter_l0out)
            l0_out = ''
            for out in iter_l0out:
                l0_out += f"{'{:07b}'.format(int(out))}"
            return l0_out

        print("\n<- got BNN response:")
        ether.show()
        bnn_resp = ether[BNN]

        prev_input = bfrt_bnn.inference_output[f'{bnn_resp.input_offset_cp}']['input']
        print(f'Previous input: {int(prev_input, 16)}')

        # MLP verification (using current dynamic weights)
        if current_l1_w is not None and current_l2_w is not None:
            mlp = MLP(nn[0], [nn[1]], nn[-1])
            w_mlp = hex_lists_to_ints(current_l1_w, current_l2_w)
            expected = mlp.do_inference(int(prev_input, 16), w_mlp, verbose=True)
        else:
            expected = None

        if args.arch == 'wide':
            conf_score = bnn_resp.l1_out
            obtained = bnn_resp.l2_out
            print(f'obtained: l0: {resp[BNN].l0_out} l1: {conf_score} l2: {obtained}')
        else:
            if args.arch == 'dense':
                conf_score = handle_conf_score([
                    bnn_resp.l0_out_1, bnn_resp.l0_out_2, bnn_resp.l0_out_3,
                    bnn_resp.l0_out_4, bnn_resp.l0_out_5, bnn_resp.l0_out_6])
            elif args.arch == 'tiny':
                conf_score = handle_conf_score([
                    bnn_resp.l0_out_1, bnn_resp.l0_out_2,
                    bnn_resp.l0_out_3, bnn_resp.l0_out_4])
            else:
                raise ValueError(f"Unknown model type: {args.arch}")
            obtained = bnn_resp.l1_out
            print(f'obtained: l0: {hex(int(conf_score, 2))} l1: {obtained}')

        print(f'l0_popcount: {bnn_resp.l0_popcount}  '
              f'is_pred_confident: {bnn_resp.is_pred_confident}')

        if expected is not None:
            color = '\033[92m' if expected == obtained else '\033[91m'
            print(f'{color}Result is {"NOT " if expected != obtained else ""}matching!\033[0m')

        bfrt_bnn.inference_output[f'{bnn_resp.input_offset_cp}']['last_layer'] = hex(int(conf_score, 2))
        bfrt_bnn.inference_output[f'{bnn_resp.input_offset_cp}']['result'] = obtained

        # --- Confidence-based branching ---
        offset = bnn_resp.input_offset_cp
        is_confident = bnn_resp.is_pred_confident
        l1_out = bnn_resp.l1_out
        is_malicious = (l1_out & 0x02) != 0

        if is_confident == 0:
            # UNCERTAIN — collect as critical sample
            uncertain_count += 1
            full_features = stored_features.pop(offset, None)
            if full_features is not None:
                teacher.model.eval()
                with torch.no_grad():
                    x = torch.tensor(full_features, dtype=torch.float32).unsqueeze(0)
                    x = x.to(teacher.device)
                    logits = teacher.model(x)
                    pseudo_label = logits.argmax(1).item()

                with retraining_lock:
                    critical_samples_X.append(full_features)
                    critical_samples_Y.append(pseudo_label)
                    n_critical = len(critical_samples_X)

                print(f"[UNCERTAIN] Sample #{n_critical} collected "
                      f"(teacher label={pseudo_label})")

                if (n_critical >= CRITICAL_RETRAIN_SAMPLES
                        and not retraining_triggered):
                    retraining_triggered = True
                    print(f"\n[RETRAIN] Threshold {CRITICAL_RETRAIN_SAMPLES} reached! "
                          f"Spawning retraining thread.")
                    Thread(target=retrain_and_redeploy, daemon=True).start()
            else:
                print(f"[WARN] No stored features for offset {offset}")

        elif is_confident == 1 and is_malicious:
            # CONFIDENT + MALICIOUS — alert
            alert_count += 1
            stored_features.pop(offset, None)
            print(f"[ALERT #{alert_count}] Confident malicious prediction (l1_out={l1_out})")

        else:
            # Confident + legit should be dropped by P4; clean up if it arrives
            stored_features.pop(offset, None)

    except Exception as e:
        print(f"[BNN] Unexpected response error: {e}")


# ---------------------------------------------------------------------------
#  Retraining
# ---------------------------------------------------------------------------

def retrain_and_redeploy():
    """Retrain student BNN with OG + critical samples, redeploy to P4."""
    global student, current_l1_w, current_l2_w, confident_score_array, bfrt_bnn

    print("\n" + "=" * 60)
    print("  RETRAINING TRIGGERED")
    print("=" * 60)

    # 1. Snapshot critical samples under lock
    with retraining_lock:
        X_critical = np.array(critical_samples_X[-CRITICAL_RETRAIN_SAMPLES:])
        Y_critical = np.array(critical_samples_Y[-CRITICAL_RETRAIN_SAMPLES:])

    print(f"Critical samples: {len(X_critical)} "
          f"(benign={np.sum(Y_critical == 0)}, malicious={np.sum(Y_critical == 1)})")

    # 2. Build retraining dataset: OG subset + critical samples
    og_size = min(OG_RETRAIN_SAMPLES, len(X_train_full))
    og_idx = np.random.choice(len(X_train_full), size=og_size, replace=False)
    X_og = X_train_full[og_idx][:, shap_feat_idx]
    Y_og = Y_train_full[og_idx]

    X_critical_shap = X_critical[:, shap_feat_idx]

    X_retrain = np.vstack([X_og, X_critical_shap])
    Y_retrain = np.hstack([Y_og, Y_critical])

    shuf = np.random.permutation(len(X_retrain))
    X_retrain, Y_retrain = X_retrain[shuf], Y_retrain[shuf]

    print(f"Retraining dataset: {len(X_retrain)} "
          f"({og_size} OG + {len(X_critical)} critical, teacher-labeled)")

    # 3. Retrain student BNN
    arch_name = ARCH_MAP[args.arch][0]
    retrained = SimpleTrainer(arch_name, 'cpu')
    retrained.reset_model()
    retrained.epochs = RETRAINING_EPOCHS
    results = retrained.train(X_retrain, Y_retrain, verbose=True)
    print(f"Retrained accuracy: {results['final_accuracy']:.4f}")

    retrain_dir = os.path.join(RES_DIR, 'retrain')
    os.makedirs(retrain_dir, exist_ok=True)
    retrained.save_model(os.path.join(retrain_dir, 'retrained_student.pth'))

    # 4. Re-analyze confidence
    print("\nRe-analyzing confidence distribution...")
    val_X = X_val_full[:, shap_feat_idx]
    _, _, new_confident_scores = analyze_confidence_distribution(
        retrained, val_X, Y_val_full, retrain_dir)
    confident_score_array = new_confident_scores

    # 5. Extract new weights
    new_l1_w, new_l2_w = BNNPipeline.extract_weights_hex(retrained.model)
    current_l1_w = new_l1_w
    current_l2_w = new_l2_w

    # 6. Redeploy to P4
    print("\nRedeploying to P4...")
    bfrt_bnn.clear_weights_tb()
    bfrt_bnn.load_weights_tb(new_l1_w, new_l2_w)
    bfrt_bnn.load_confidence_tb(confident_score_array)

    student = retrained

    print("\n" + "=" * 60)
    print("  RETRAINING COMPLETE — New weights deployed")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
#  Packet listener threads
# ---------------------------------------------------------------------------

def cpu_listener(stop_event: Event):
    """Thread: listen on CPU port and forward/trigger BNN."""
    print(f"[CPU Listener] starting on {FEATURE_EXTRACTOR_CPU_INTF}")
    sniff(
        iface=FEATURE_EXTRACTOR_CPU_INTF,
        prn=process_cpu_packet,
        promisc=True,
        store=False,
        stop_filter=lambda _: stop_event.is_set(),
        count=args.max_flows
    )
    print("[CPU Listener] stopped.")


def bnn_listener(stop_event: Event):
    """Thread: listen on BNN->CPU interface and print results."""
    print(f"[BNN Listener] starting on {BNN_TO_CPU_INTF}")
    sniff(
        iface=BNN_TO_CPU_INTF,
        prn=handle_bnn_response,
        promisc=True,
        store=False,
        stop_filter=lambda _: stop_event.is_set(),
        count=args.max_flows
    )
    print("[BNN Listener] stopped.")


# ---------------------------------------------------------------------------
#  Initial training pipeline
# ---------------------------------------------------------------------------

def initial_training_pipeline():
    """Train teacher, select SHAP features, train student, deploy to P4."""
    global teacher, student, shap_feat_idx, confident_score_array
    global current_l1_w, current_l2_w, bfrt_bnn
    global X_train_full, Y_train_full, X_val_full, Y_val_full, RES_DIR

    arch_name = ARCH_MAP[args.arch][0]
    RES_DIR = os.path.join(args.results_dir, f'tf_retrain_{arch_name}')
    os.makedirs(RES_DIR, exist_ok=True)
    os.makedirs(os.path.join(RES_DIR, 'weights'), exist_ok=True)

    # ── Step 1: Load dataset ─────────────────────────────────────────────
    print("\n[1/6] Loading dataset...")
    X, Y = load_dataset(args.dataset_name)
    X_train_full = X
    Y_train_full = Y

    X_tr, X_test, Y_tr, Y_test = train_test_split(
        X, Y, train_size=0.8, random_state=42, stratify=Y)
    X_test, X_val, Y_test, Y_val = train_test_split(
        X_test, Y_test, train_size=0.9, random_state=42, stratify=Y_test)

    X_val_full = X_val
    Y_val_full = Y_val

    print(f"  Training:   {len(X_tr):,}")
    print(f"  Validation: {len(X_val):,}")
    print(f"  Test:       {len(X_test):,}")
    print(f"  Features:   {X_tr.shape[1]}")

    # ── Step 2: Train teacher ────────────────────────────────────────────
    print("\n[2/6] Training teacher (binocular_teacher)...")
    teacher = SimpleTrainer('binocular_teacher', 'cpu')
    teacher.reset_model(nn_input_size=X_tr.shape[1])
    teacher.train(X_tr, Y_tr, verbose=True)
    teacher.save_model(os.path.join(RES_DIR, 'weights', 'teacher.pth'))

    # ── Step 3: SHAP feature selection ───────────────────────────────────
    print("\n[3/6] Computing SHAP feature importance...")
    shap_result = teacher.shap_model(
        background_data=X_tr,
        explain_data=X_val,
        force_recompute=True)

    shap_feat_idx = shap_result['feature_indices'][:nn[0]]
    print(f"  Selected {len(shap_feat_idx)} SHAP features (top of {X_tr.shape[1]})")

    # ── Step 4: Train student BNN ────────────────────────────────────────
    print(f"\n[4/6] Training student BNN ({arch_name})...")
    student = SimpleTrainer(arch_name, 'cpu')
    student.reset_model()
    student.train(X_tr[:, shap_feat_idx], Y_tr, verbose=True)
    student.save_model(os.path.join(RES_DIR, 'weights', 'student_initial.pth'))

    # ── Step 5: Confidence analysis ──────────────────────────────────────
    print("\n[5/6] Analyzing confidence distribution...")
    _, _, confident_score_array = analyze_confidence_distribution(
        student, X_val[:, shap_feat_idx], Y_val, RES_DIR)
    print(f"  Confident popcount values: {confident_score_array}")

    # ── Step 6: Deploy to P4 ─────────────────────────────────────────────
    print("\n[6/6] Deploying to P4 data plane...")
    current_l1_w, current_l2_w = BNNPipeline.extract_weights_hex(student.model)
    print(f"  L0 weights: {len(current_l1_w)} neurons")
    print(f"  L1 weights: {len(current_l2_w)} neurons")

    bfrt_bnn = BNNPipeline(args.arch, bfrt=bfrt, input_length=nn[0])
    bfrt_bnn.load_pop_tb()
    bfrt_bnn.load_weights_tb(current_l1_w, current_l2_w)
    bfrt_bnn.load_confidence_tb(confident_score_array)

    print("\n" + "=" * 60)
    print("  INITIAL TRAINING & DEPLOYMENT COMPLETE")
    print("=" * 60)


# ---------------------------------------------------------------------------
#  Argument parsing
# ---------------------------------------------------------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Binocular Controller with Online Retraining")
    parser.add_argument("--arch", default='dense', type=str,
                        choices=list(ARCH_MAP.keys()),
                        help="BNN architecture (tiny, dense, wide).")
    parser.add_argument("--dataset-name", type=none_or_str,
                        default='CICIDS2017', help="Training dataset name")
    parser.add_argument("--results-dir", type=str,
                        default='results', help="Directory to save results")
    parser.add_argument("--max-flows", type=int,
                        default=CONCURRENT_ACTIVE_FLOWS,
                        help="Max packets per listener (debug cap)")
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    global args, BNN
    global CRITICAL_RETRAIN_SAMPLES, OG_RETRAIN_SAMPLES, RETRAINING_EPOCHS

    args = parse_args(sys.argv[1:])

    arch_name, BNNClass = ARCH_MAP[args.arch]
    BNN = BNNClass
    bind_layers(Ether, BNN, type=BNN_TYPE_ETHER)

    # Load experiment config
    exp_cfg = get_cfg('experiments')
    section = f'{EXPERIMENT_NAME}-{arch_name.upper()}'
    CRITICAL_RETRAIN_SAMPLES = exp_cfg.getint(section, 'CRITICAL_RETRAIN_SAMPLES')
    OG_RETRAIN_SAMPLES = exp_cfg.getint(section, 'OG_RETRAIN_SAMPLES')
    RETRAINING_EPOCHS = exp_cfg.getint(section, 'RETRAINING_EPOCHS')

    print(f"Architecture: {arch_name}")
    print(f"Retraining config: critical={CRITICAL_RETRAIN_SAMPLES}, "
          f"og={OG_RETRAIN_SAMPLES}, epochs={RETRAINING_EPOCHS}")
    print(f"Max flows per listener: {args.max_flows}")

    # Phase 1: Training pipeline
    initial_training_pipeline()

    # Phase 2: Packet listeners
    stop_event = Event()
    t_cpu = Thread(target=cpu_listener, args=(stop_event,), daemon=True)
    t_bnn = Thread(target=bnn_listener, args=(stop_event,), daemon=True)

    t_cpu.start()
    t_bnn.start()

    print("[Main] Listener threads started. Press Ctrl+C to stop.")
    try:
        while True:
            t_cpu.join(timeout=30)
            t_bnn.join(timeout=30)
            with retraining_lock:
                n_crit = len(critical_samples_X)
            retrain_status = "DONE" if retraining_triggered else f"{n_crit}/{CRITICAL_RETRAIN_SAMPLES}"
            print(f"[Status] Critical: {retrain_status} | "
                  f"Alerts: {alert_count} | Uncertain: {uncertain_count}")
            if not t_cpu.is_alive() and not t_bnn.is_alive():
                break
    except KeyboardInterrupt:
        print("\n[Main] Stopping...")
        stop_event.set()
        t_cpu.join(timeout=5)
        t_bnn.join(timeout=5)

    json.dump(bfrt_bnn.inference_output,
              open(os.path.join(args.results_dir,
                                f'inference_output_{args.arch}.json'), 'w'),
              indent=4)
    print(f"[Main] Stopped. Critical: {len(critical_samples_X)}, Alerts: {alert_count}.")


if __name__ == "__main__":
    main()
