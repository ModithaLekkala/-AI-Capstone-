import pandas as pd
from scapy.all import sendp
from scapy.layers.l2 import Ether
from configparser import ConfigParser
import os
import json
from helpers.pycommon import BNNFeaturesHeader, DUMMY_ETHER_SRC, DUMMY_ETHER_DST, FEATURES_TYPE_ETHER, CONCURRENT_ACTIVE_FLOWS
from helpers.utils import get_cfg

###########################################
# BNN FEATURES EXTRACTOR EMULATOR
###########################################


TEST_SET='/home/sgeraci/Desktop/datasets/CICIDS2017/full_cicids2017_balanced.csv'
CICIDS2017_CONFIG = 'cicids2017'
FEATURE_EXTRACTOR_CPU_INTF = 'veth5'

def main():
    dataset_cfg = get_cfg(CICIDS2017_CONFIG)
    selected_features = json.loads(dataset_cfg.get('DATASET', 'SELECTED_FEATURES'))

    print('Loading test set...', end='')
    flows_test_set = pd.read_csv(TEST_SET)
    flows_test_set = flows_test_set[selected_features]
    print(' done.')

    print(f'Sampling {CONCURRENT_ACTIVE_FLOWS} flows from test set...', end='')
    flows_test_set = flows_test_set.sample(n=CONCURRENT_ACTIVE_FLOWS, random_state=1).reset_index(drop=True)
    print(' done.')
    
    print('Flow features packets are creating...', end='')
    packet_list = []
    for ix, flow in enumerate(flows_test_set.iterrows()):
        packet = (Ether(src=DUMMY_ETHER_SRC, dst=DUMMY_ETHER_DST, type=FEATURES_TYPE_ETHER) /
                    BNNFeaturesHeader(
                        sbytes    = int(flow[1]['sbytes']),
                        dbytes    = int(flow[1]['dbytes']),
                        spkts     = int(flow[1]['spkts']),
                        dpkts     = int(flow[1]['dpkts']),
                        smean     = int(flow[1]['smeansz']),
                        dmean     = int(flow[1]['dmeansz']),
                        smaxbytes = int(flow[1]['smaxbytes']),
                        sminbytes = int(flow[1]['sminbytes']),
                        dmaxbytes = int(flow[1]['dmaxbytes']),
                        dminbytes = int(flow[1]['dminbytes']),
                        fin_cnt   = int(flow[1]['fin_cnt']),
                        syn_cnt   = int(flow[1]['syn_cnt']),
                        rst_cnt   = int(flow[1]['rst_cnt']),
                        psh_cnt   = int(flow[1]['psh_cnt']),
                        ack_cnt   = int(flow[1]['ack_cnt']),
                        ece_cnt   = int(flow[1]['ece_cnt'])
                    )
                )
        
        # if(ix % 5 == 0):
        print(f'\n{packet[BNNFeaturesHeader].summary()}')

        packet_list.append(packet)

    print('\ndone.')
    print('Sending packets...', end='')
    sendp(packet_list, iface=FEATURE_EXTRACTOR_CPU_INTF)


if __name__ == "__main__":
    main()