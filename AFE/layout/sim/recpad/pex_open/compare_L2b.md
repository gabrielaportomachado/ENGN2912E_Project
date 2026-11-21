# compare.py L2b: AFE/layout/sim/recpad/pex_open against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27565 | -0.00572 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 972.5 | -25.17 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.0747 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.42 | -0.2654 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.742 | -0.1933 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.83 | -0.1557 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28319 | -0.004604 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 408.49 | -13.61 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6501 | -0.0001 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3236 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.977 | -0.2947 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.736 | -0.1583 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.858 | -0.1293 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.2414 | -0.004482 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 634.43 | -19.07 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0775 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.962 | -0.2663 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.016 | -0.182 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.846 | -0.1412 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1532 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7436 | +0.0113 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7416 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3941 | +0.007589 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.9018 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5044 | +0.00905 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.91 | +0.03077 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.63 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5694e+05 | -6082 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8706e+05 | -2426 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.27 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5006e+05 | -3692 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.391 | -10.49 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.6662 | +0.08632 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66577 | +0.08619 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63908 | +0.08112 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.4781 | +0.05394 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.61891 | +0.05158 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61698 | +0.05124 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50949 | +0.03623 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.25639 | +0.01173 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.6374 | +0.06501 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63654 | +0.06482 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58185 | +0.05591 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36169 | +0.02674 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.94383 | -1.459 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2053 | +0.01578 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2373 | +0.01699 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.751 | -0.1565 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.687 | -8.439 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.26 | -8.351 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051826 | -0.004984 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1633 | +0.01386 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1783 | +0.03333 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.822 | -0.2124 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.914 | +16.45 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.469 | -1.475 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039711 | -0.002277 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1654 | +0.01433 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1803 | +0.03539 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.82 | -0.2293 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.751 | +10.21 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.858 | -2.112 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.235 | +18.14 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1492 | +0.007868 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 19.765 | +19.15 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.3584 | +0.5578 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.264 | +30.03 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.5161 | +0.0556 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.7289 | +0.1008 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.5115 | +2.523 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.5735 | +3.239 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 8.1997 | +3.823 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 9.6642 | +4.204 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.534e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6511 | +0.0001279 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 273 | +103.5 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -204.01 | -208 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -7.1344 | -6.361 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.9757 | +0.1839 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.4576 | +4.803 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.4815 | +5.083 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 7.3642 | +4.628 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 8.1039 | +1.257 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.956e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +3.475e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 233.19 | +179.9 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | -54.508 | -54.51 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -7.082 | -6.757 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0439 | -0.05268 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 5.5928 | +3.793 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.5979 | +4.202 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 8.5546 | +4.753 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 11.291 | +2.869 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +8.649e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6508 | +0.0001388 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 853.11 | +795.2 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -256.54 | -248.7 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -7.5641 | -7.029 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4251 | +3.717 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1317 | +1.09 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.696e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.5118 | +3.62 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.7038 | +1.187 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.189e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6303 | +3.746 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1416 | +1.135 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.113e-06 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.789 | -0.2622 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 975.11 | -22.47 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00059 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.095322 | +0.02529 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.816 | -0.216 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 409.06 | -12.67 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6592 | +0.02248 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.81 | -0.2371 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 635.82 | -17.44 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6644 | +0.05072 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 95.923 | +94.98 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 179.26 | +177.5 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 181.25 | +180.2 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.267 | +9.742 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6626 | -0.005696 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.6645 | -0.1998 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 10.809 | +1.39 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.6038 | -0.02068 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.5698 | -0.1786 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9314 | -0.0003435 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.6075 | +0.06892 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.5803 | -0.179 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7376 | -0.0009171 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: PASS  (90 PASS, 0 WARN, 0 FAIL, 0 missing)
