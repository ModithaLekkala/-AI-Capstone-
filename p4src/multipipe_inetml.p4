#include "common/headers.p4"
#include "tf_feature_extr/feature_extractor.p4"
// #include "tf_bnn_exec_126-42-2_7nr/tofino_mlp.p4"

// Switch(features_collector, bnn_executor) main;
// Switch(bnn_executor) main;
Switch(features_collector) main;