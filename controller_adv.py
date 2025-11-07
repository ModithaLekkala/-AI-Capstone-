from threading import Thread, Event
from scapy.all import sniff, sendp, Ether, raw, bind_layers, AsyncSniffer
from helpers.pycommon import BNNFeaturesHeader, BNNWide, BNNDense, BNNTiny, DUMMY_ETHER_SRC, DUMMY_ETHER_DST, BNN_TYPE_ETHER, FEATURES_TYPE_ETHER, nn, l1_w, l2_w, CONCURRENT_ACTIVE_FLOWS
from helpers.mlp import MLP
from helpers.bfrt_bnn import BNNPipeline
from helpers.utils import hex_lists_to_ints, none_or_str
from ml_helpers.trainer import Trainer
from ml_helpers.utils import get_cfg
import argparse
import sys
import json
import os
import pandas as pd

FEATURE_EXTRACTOR_CPU_INTF = 'veth5'
BNN_TO_CPU_INTF = 'veth7'
CPU_TO_BNN_INTF = 'veth8'

input_offset = 0
inference_output = {}
BNN = None
args = None

bind_layers(Ether, BNNFeaturesHeader, type=FEATURES_TYPE_ETHER)

def create_shap_dataset(dataset_name, arch='dense'):
    """Simple SHAP dataset creation: compute SHAP, get top 126 features, filter dataset."""
    
    dataset_dir = f"/home/sgeraci/Desktop/datasets/{dataset_name}"
    original_dataset = f"{dataset_dir}/bin_{dataset_name}_168b"
    shap_dataset = f"{dataset_dir}/bin_{dataset_name}_shap126.csv"
    
    # Check if SHAP dataset already exists
    if os.path.exists(shap_dataset):
        print(f"SHAP dataset already exists: {shap_dataset}")
        return shap_dataset
    
    print(f"Creating SHAP dataset for {dataset_name}...")
    
    # Train model and compute SHAP
    trainer = Trainer(model_name='full', dataset_name=dataset_name, arch=arch)
    trainer.train_model()
    
    # Find SHAP results
    shap_dirs = [d for d in os.listdir(trainer.results_dir) if d.startswith('shap_')]
    if not shap_dirs:
        print("No SHAP results found!")
        return None
    
    # Get top 126 features
    shap_dir = os.path.join(trainer.results_dir, sorted(shap_dirs)[-1])
    importance_file = os.path.join(shap_dir, "mean_abs_shap_importance.csv")
    importance_df = pd.read_csv(importance_file)
    top_features = importance_df.head(126)['feature'].tolist()
    
    # Filter original dataset
    print(f"Filtering dataset to top 126 features...")
    df = pd.read_csv(original_dataset)
    target_col = df.columns[-1]
    filtered_df = df[top_features + [target_col]]
    
    # Save SHAP dataset
    filtered_df.to_csv(shap_dataset, index=False)
    print(f"SHAP dataset saved: {shap_dataset} (shape: {filtered_df.shape})")
    
    return shap_dataset

def process_cpu_packet(pkt):
    """Handle a packet arriving on the CPU port: extract features and trigger BNN."""
    global args, input_offset, inference_output, bfrt_bnn

    try:
        packet = Ether(raw(pkt))
        if packet.type != FEATURES_TYPE_ETHER:
            return  # not a feature-extractor packet; ignore silently

        print('\nPacket received from feature extractor pipeline:')
        cpu_header = packet[BNNFeaturesHeader]
        print(cpu_header.summary())
        
        bnn_input = cpu_header.to_hex()
        print('Load features into BNN input registers:')

        # Make sixteen 4-digit substrings:
        if args.arch == 'wide':
            bnn_input = bnn_input[:32] #DEBUG PURPOSE, TO REMOVE IN THE END
            bnn_input = '{:0128b}'.format(int(bnn_input, 16))
        elif args.arch == 'dense':
            bnn_input = bnn_input[:33] #DEBUG PURPOSE, TO REMOVE IN THE END
            bnn_input = '{:0140b}'.format(int(bnn_input, 16))
        elif args.arch == 'tiny':
            bnn_input = bnn_input[:25] #DEBUG PURPOSE, TO REMOVE IN THE END
            bnn_input = '{:098b}'.format(int(bnn_input, 16))
        # print(f'Input chunks: {input_chunks}')

        loaded_offset = bfrt_bnn.load_bnn_input_reg(bnn_input)

        # Trigger BNN pipeline
        trigger = Ether(src=DUMMY_ETHER_SRC, dst=DUMMY_ETHER_DST, type=BNN_TYPE_ETHER) / BNN(input_offset=loaded_offset, input_offset_cp=loaded_offset)
        print('Send trigger packet to BNN pipeline.')
        sendp(trigger, iface=CPU_TO_BNN_INTF, verbose=False)

    except AssertionError as e:
        print(f"[CPU->BNN] Input error: {e}")
    except Exception as e:
        print(f"[CPU->BNN] Unexpected processing error: {e}")

def handle_bnn_response(resp):

    global args, input_offset, inference_output
    """Handle a packet arriving from the BNN interface."""
    try:
        if not resp:
            print("✗ no reply")
            return

        ether = Ether(raw(resp))
        if BNN not in ether:
            # Not a BNN packet; ignore (or print if you prefer)
            return

        def handle_conf_score(iter_l0out):
            print('Compose l0_out from parts:', iter_l0out)
            l0_out = ''
            for out in iter_l0out:
                l0_out+=f"{'{:07b}'.format(int(out))}"
            return l0_out

        print("← got BNN response:")
        ether.show()
        bnn_resp = ether[BNN]

        # print(bfrt_bnn.inference_output)


        prev_input = bfrt_bnn.inference_output[f'{bnn_resp.input_offset_cp}']['input']
        print(f'Previous input: {int(prev_input,16)}')
        mlp = MLP(nn[0], [nn[1]], nn[-1])
        w_mlp = hex_lists_to_ints(l1_w, l2_w)
        expected = mlp.do_inference(int(prev_input , 16), w_mlp, verbose=True)
        # print(f'Expected output for previous input: {expected}')

        if args.arch == 'wide':
            conf_score = bnn_resp.l1_out
            obtained = bnn_resp.l2_out
            print(f'obtained: l0: {resp[BNN].l0_out} l1: {conf_score} l2: {obtained}')

        else:
            if args.arch == 'dense':
                conf_score = handle_conf_score([bnn_resp.l0_out_1, bnn_resp.l0_out_2, bnn_resp.l0_out_3, bnn_resp.l0_out_4, bnn_resp.l0_out_5, bnn_resp.l0_out_6])
            elif args.arch == 'tiny':
                conf_score = handle_conf_score([bnn_resp.l0_out_1, bnn_resp.l0_out_2, bnn_resp.l0_out_3, bnn_resp.l0_out_4])
            else:
                raise ValueError(f"Unknown model type: {args.arch}")
            obtained = bnn_resp.l1_out
            print(f'obtained: l0: {hex(int(conf_score, 2))} l1: {obtained}')

        color = '\033[92m' if expected == obtained else '\033[91m'
        print(f'{color}Result is {"NOT " if not expected == obtained else ""}matching!\033[0m')

        bfrt_bnn.inference_output[f'{bnn_resp.input_offset_cp}']['last_layer'] = hex(int(conf_score, 2))
        bfrt_bnn.inference_output[f'{bnn_resp.input_offset_cp}']['result'] = obtained


    except Exception as e:
        print(f"[BNN] Unexpected response error: {e}")

def cpu_listener(stop_event: Event):
    """Thread: listen on CPU port and forward/trigger BNN."""
    print(f"[CPU Listener] starting on {FEATURE_EXTRACTOR_CPU_INTF}")
    sniff(
        iface=FEATURE_EXTRACTOR_CPU_INTF,
        prn=process_cpu_packet,
        promisc=True,
        store=False,
        stop_filter=lambda _: stop_event.is_set(),
        count=CONCURRENT_ACTIVE_FLOWS
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
        count=CONCURRENT_ACTIVE_FLOWS
    )
    print("[BNN Listener] stopped.")


def parse_args(args):
    parser = argparse.ArgumentParser(description="UNSW_NB15 Training")
    parser.add_argument("--arch", default='dense', type=str, help="One between (tiny, dense, wide).")
    parser.add_argument("--dataset-name", type=none_or_str, default='UNSW-NB15-custom', help="Dataset")
    parser.add_argument("--results-dir", type=str, default='p4src/results', help="Directory to save results")

    parsed_args = parser.parse_args(args)

    return parsed_args

def main():
    global args
    args = parse_args(sys.argv[1:])

    global BNN
    if args.arch == 'dense':
        print("→ Using Dense model architecture.")
        BNN=BNNDense
    else:
        raise ValueError(f"Unknown model type: {args.arch}")
    bind_layers(Ether, BNN, type=BNN_TYPE_ETHER)

    global bfrt_bnn
    bfrt_bnn = BNNPipeline(args.arch, bfrt=bfrt, input_length=nn[0])
    if args.arch == 'dense':
        bfrt_bnn.load_pop_tb()
        bfrt_bnn.load_weights_tb(l1_w, l2_w)

    # TODO: implement tiny weight loading
    # TODO: implement wide weight loading
    
    print("→ BNN initialization complete.\n")

    stop_event = Event()
    t_cpu = Thread(target=cpu_listener, args=(stop_event,), daemon=True)
    t_bnn = Thread(target=bnn_listener, args=(stop_event,), daemon=True)

    t_cpu.start()
    t_bnn.start()

    print("[Main] Threads started. Press Ctrl+C to stop.")
    try:
        # Keep the main thread alive while workers run
        while True:
            t_cpu.join(timeout=60)
            t_bnn.join(timeout=60)
            if not t_cpu.is_alive() or not t_bnn.is_alive():
                break
    except KeyboardInterrupt:
        print("\n[Main] Stopping…")
        stop_event.set()
        t_cpu.join()
        t_bnn.join()

    json.dump(bfrt_bnn.inference_output, open(f'inference_output_{args.arch}.json', 'w'), indent=4)
    print("[Main] All listeners stopped. Bye.")

if __name__ == "__main__":
    main()
