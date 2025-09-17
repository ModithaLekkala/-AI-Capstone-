#define FLOWS_NO 65535
#define FLOW_MATURE_TIME 8
/* 2 x BIDIRECTIONAL_FLOW_MATURE_TIME=FLOW_MATURE_TIME*/
#define BIDIRECTIONAL_FLOW_MATURE_TIME 16

#define TCP_PKT hdr.tcp.isValid()
#define RESUB_PKT ig_intr_md.resubmit_flag == 1
#define NOT_RESUB_PKT ig_intr_md.resubmit_flag == 0
#define FORWARD_DIR_PKT meta.flow_dir == 1
#define BACKWARD_DIR_PKT meta.flow_dir == 0

#define MIRRORED ig_intr_md.resubmit_flag == 0
#define SEND_TO(output_port) ig_tm_md.ucast_egress_port=##output_port;


#define PKT_TYPE_SYN 0;
#define PKT_TYPE_SYN_FIN 1;
#define PKT_TYPE_SYN_ECE 2;
#define PKT_TYPE_SYNACK_ECE 3;
#define PKT_TYPE_SYN_PSH 4;
#define PKT_TYPE_ACK 5;
#define PKT_TYPE_ACK_FIN 6;
#define PKT_TYPE_ACK_ECE 7;
#define PKT_TYPE_SYNACK 8;
#define PKT_TYPE_SYNACK_PSH 9;
#define PKT_TYPE_SYNACK_FIN 10;
#define PKT_TYPE_FIN 11;
#define PKT_TYPE_RST 12;


#define PROTO_TCP 0
#define PROTO_UDP 1
#define PROTO_ICMP 2
#define PROTO_GRE 3
#define PROTO_OSPF 4
#define PROTO_OTHER 5