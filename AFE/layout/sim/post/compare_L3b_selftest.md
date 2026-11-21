# compare.py L3b: baseline (selftest) against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| bias_startup | ff85 | t90_n8_ms | 1.0052 | 1.0052 | +0 | <= 4500 | PASS |
| bias_startup | ff85 | settled_n8 | 1 | 1 | +0 | >= 1 | PASS |
| bias_startup | ff85 | vcm_v | 1.6486 | 1.6486 | +0 | |change| <= 0.005 | PASS |
| bias_startup | ff85 | vrs_v | 1.2221 | 1.2221 | +0 | |change| <= 0.03 | PASS |
| bias_startup | ff85 | i_sink_n8_ua | 272.94 | 272.94 | +0 | x / baseline 0.9 .. 1.1 | PASS |
| bias_startup | ss-40 | t90_n8_ms | 3564.8 | 3564.8 | +0 | <= 4500 | PASS |
| bias_startup | ss-40 | settled_n8 | 1 | 1 | +0 | >= 1 | PASS |
| bias_startup | ss-40 | vcm_v | 1.6491 | 1.6491 | +0 | |change| <= 0.005 | PASS |
| bias_startup | ss-40 | vrs_v | 0.81435 | 0.81435 | +0 | |change| <= 0.03 | PASS |
| bias_startup | ss-40 | i_sink_n8_ua | 106.16 | 106.16 | +0 | x / baseline 0.9 .. 1.1 | PASS |
| bias_startup | typ | t90_n8_ms | 3.7147 | 3.7147 | +0 | <= 4500 | PASS |
| bias_startup | typ | settled_n8 | 1 | 1 | +0 | >= 1 | PASS |
| bias_startup | typ | vcm_v | 1.6489 | 1.6489 | +0 | |change| <= 0.005 | PASS |
| bias_startup | typ | vrs_v | 1.0282 | 1.0282 | +0 | |change| <= 0.03 | PASS |
| bias_startup | typ | i_sink_n8_ua | 169.5 | 169.5 | +0 | x / baseline 0.9 .. 1.1 | PASS |
| top_e2e | ff85 | offset_lsb | -40.304 | -40.304 | +0 | |change| <= 15 | PASS |
| top_e2e | ff85 | inl_lo_lsb | 1.9954 | 1.9954 | +0 | <= 3.1 | PASS |
| top_e2e | ff85 | amp_minus_adc_lsb | 0.077711 | 0.077711 | +0 | <= 0.5 | PASS |
| top_e2e | ff85 | gain_sine_code_db | 59.853 | 59.853 | +0 | 58.8 .. 61 | PASS |
| top_e2e | ff85 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| top_e2e | ff85 | inl_all_lsb | 5.1116 | 5.1116 | +0 |  |  |
| top_e2e | ff85 | vout_min_v | 1.2134 | 1.2134 | +0 |  |  |
| top_e2e | ff85 | vout_max_v | 2.1523 | 2.1523 | +0 |  |  |
| top_e2e | ff85 | kick_max_mv | 448.3 | 448.3 | +0 |  |  |
| top_e2e | ss-40 | offset_lsb | -21.983 | -21.983 | +0 | |change| <= 15 | PASS |
| top_e2e | ss-40 | inl_lo_lsb | 0.40727 | 0.40727 | +0 | <= 1 | PASS |
| top_e2e | ss-40 | amp_minus_adc_lsb | 0.054056 | 0.054056 | +0 | <= 0.5 | PASS |
| top_e2e | ss-40 | gain_sine_code_db | 59.978 | 59.978 | +0 | 59 .. 61 | PASS |
| top_e2e | ss-40 | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| top_e2e | ss-40 | inl_all_lsb | 0.96037 | 0.96037 | +0 |  |  |
| top_e2e | ss-40 | vout_min_v | 1.1501 | 1.1501 | +0 |  |  |
| top_e2e | ss-40 | vout_max_v | 2.1503 | 2.1503 | +0 |  |  |
| top_e2e | ss-40 | kick_max_mv | 493.29 | 493.29 | +0 |  |  |
| top_e2e | typ | offset_lsb | -30.266 | -30.266 | +0 | |change| <= 15 | PASS |
| top_e2e | typ | inl_lo_lsb | 0.78232 | 0.78232 | +0 | <= 1 | PASS |
| top_e2e | typ | amp_minus_adc_lsb | 0.069007 | 0.069007 | +0 | <= 0.5 | PASS |
| top_e2e | typ | gain_sine_code_db | 59.994 | 59.994 | +0 | 59 .. 61 | PASS |
| top_e2e | typ | unresolved | 0 | 0 | +0 | <= 0 | PASS |
| top_e2e | typ | inl_all_lsb | 2.7895 | 2.7895 | +0 |  |  |
| top_e2e | typ | vout_min_v | 1.1497 | 1.1497 | +0 |  |  |
| top_e2e | typ | vout_max_v | 2.1513 | 2.1513 | +0 |  |  |
| top_e2e | typ | kick_max_mv | 444.26 | 444.26 | +0 |  |  |
| top_supply | ff-40 | dt_max_lsb | 0.04 | 0.04 | +0 | <= 0.5 | PASS |
| top_supply | ff-40 | dres_max_lsb | 0.559 | 0.559 | +0 | <= 0.8 | PASS |
| top_supply | ff-40 | dres_max_lsb | 0.559 | 0.559 | +0 | <= 0.5 | WARN |
| top_supply | ff-40 | failed | 0 | 0 | +0 | <= 0 | PASS |
| top_supply | ff-40 | dcode_max | 1 | 1 | +0 |  |  |
| top_supply | ff-40 | droop_dac_mv | 1.1 | 1.1 | +0 |  |  |
| top_supply | ff-40 | droop_main_mv | 6.8 | 6.8 | +0 |  |  |
| top_supply | typ | dt_max_lsb | 0.016 | 0.016 | +0 | <= 0.5 | PASS |
| top_supply | typ | dres_max_lsb | 0.174 | 0.174 | +0 | <= 0.5 | PASS |
| top_supply | typ | dres_max_lsb | 0.174 | 0.174 | +0 |  |  |
| top_supply | typ | failed | 0 | 0 | +0 | <= 0 | PASS |
| top_supply | typ | dcode_max | 1 | 1 | +0 |  |  |
| top_supply | typ | droop_dac_mv | 0.06 | 0.06 | +0 |  |  |
| top_supply | typ | droop_main_mv | 3.64 | 3.64 | +0 |  |  |
| top_xtalk | typ | victim_conv_lsb | 0.00049648 | 0.00049648 | +0 | <= 0.5 | PASS |
| top_xtalk | typ | dcode_conv | 0 | 0 | +0 |  |  |
| top_xtalk | typ | victim_peak_mv | 0.883 | 0.883 | +0 |  |  |
| top_xtalk | typ | kick_mv | 330 | 330 | +0 |  |  |
| top_xtalk | typ | floor_lsb | 0 | 0 | +0 |  |  |
| top_pwrup8 | ff85 | err_max_mv | 0.4723 | 0.4723 | +0 | <= 10 | PASS |
| top_pwrup8 | ff85 | vrs_dip_mv | 7.0923 | 7.0923 | +0 | change <= +30 | PASS |
| top_pwrup8 | ff85 | latched_before | 4 | 4 | +0 |  |  |
| top_pwrup8 | ss-40 | err_max_mv | 1.1909 | 1.1909 | +0 | <= 10 | PASS |
| top_pwrup8 | ss-40 | vrs_dip_mv | 7.596 | 7.596 | +0 | change <= +30 | PASS |
| top_pwrup8 | ss-40 | latched_before | 4 | 4 | +0 |  |  |
| top_pwrup8 | typ | err_max_mv | 0.81196 | 0.81196 | +0 | <= 10 | PASS |
| top_pwrup8 | typ | vrs_dip_mv | 7.4142 | 7.4142 | +0 | change <= +30 | PASS |
| top_pwrup8 | typ | latched_before | 4 | 4 | +0 |  |  |
| top_stim | ff85 | rec_dev_mv | 0 | 0 | +0 | <= 5 | PASS |
| top_stim | ff85 | out_dev_mv | 0.031681 | 0.031681 | +0 | <= 50 | PASS |
| top_stim | ff85 | rec_dev_mv_leak | 0 | 0 | +0 | <= 5 | PASS |
| top_stim | ff85 | out_dev_mv_leak | 0.032987 | 0.032987 | +0 | <= 50 | PASS |
| top_stim | ff85 | final_v | 1.6509 | 1.6509 | +0 | 1.6 .. 1.7 | PASS |
| top_stim | ff85 | final_v_leak | 1.6509 | 1.6509 | +0 | 1.6 .. 1.7 | PASS |
| top_stim | ff85 | t_1mv_s | 0.94941 | 0.94941 | +0 | <= 4.5 | PASS |
| top_stim | ff85 | e_swing_v | 1.1383 | 1.1383 | +0 |  |  |
| top_stim | ff85 | e_resid_mv | 1e-05 | 1e-05 | +0 |  |  |
| top_stim | ss-40 | rec_dev_mv | 1e-05 | 1e-05 | +0 | <= 5 | PASS |
| top_stim | ss-40 | out_dev_mv | 0.046056 | 0.046056 | +0 | <= 50 | PASS |
| top_stim | ss-40 | rec_dev_mv_leak | 1e-05 | 1e-05 | +0 | <= 5 | PASS |
| top_stim | ss-40 | out_dev_mv_leak | 0.033156 | 0.033156 | +0 | <= 50 | PASS |
| top_stim | ss-40 | final_v | 1.6502 | 1.6502 | +0 | 1.6 .. 1.7 | PASS |
| top_stim | ss-40 | final_v_leak | 1.6502 | 1.6502 | +0 | 1.6 .. 1.7 | PASS |
| top_stim | ss-40 | t_1mv_s | 0.65894 | 0.65894 | +0 | <= 4.5 | PASS |
| top_stim | ss-40 | e_swing_v | 0.90596 | 0.90596 | +0 |  |  |
| top_stim | ss-40 | e_resid_mv | 1e-05 | 1e-05 | +0 |  |  |
| top_stim | typ | rec_dev_mv | 0 | 0 | +0 | <= 5 | PASS |
| top_stim | typ | out_dev_mv | 0.031703 | 0.031703 | +0 | <= 50 | PASS |
| top_stim | typ | rec_dev_mv_leak | 0 | 0 | +0 | <= 5 | PASS |
| top_stim | typ | out_dev_mv_leak | 0.031606 | 0.031606 | +0 | <= 50 | PASS |
| top_stim | typ | final_v | 1.6506 | 1.6506 | +0 | 1.6 .. 1.7 | PASS |
| top_stim | typ | final_v_leak | 1.6506 | 1.6506 | +0 | 1.6 .. 1.7 | PASS |
| top_stim | typ | t_1mv_s | 0.67285 | 0.67285 | +0 | <= 4.5 | PASS |
| top_stim | typ | e_swing_v | 1.0218 | 1.0218 | +0 |  |  |
| top_stim | typ | e_resid_mv | 1e-05 | 1e-05 | +0 |  |  |

RESULT compare L3b: PASS  (64 PASS, 1 WARN, 0 FAIL, 0 missing)
