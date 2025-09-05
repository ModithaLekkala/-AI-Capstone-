#include "common/headers.p4"
#include "tofino_feature_extractor/feature_extractor.p4"
#include "tofino_bnn_executor/tofino_mlp.p4"

Switch(features_collector, bnn_executor) main;
// Switch(bnn_executor) main;
// Switch(features_collector) main;