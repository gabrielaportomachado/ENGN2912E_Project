# compare.py L2b: AFE/layout/sim/recpad/pex_leak_1n against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27565 | -0.005723 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 972.5 | -25.17 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0.001 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.0747 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.42 | -0.2654 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.742 | -0.1933 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.83 | -0.1557 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.843 | -0.1948 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.843 | -0.1948 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28301 | -0.004788 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 408.51 | -13.59 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.134 | +0.001 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3234 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.977 | -0.2947 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.737 | -0.1574 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.858 | -0.1293 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24155 | -0.004337 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 634.43 | -19.07 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.431 | +0.001 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6508 | +0.00013 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0775 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.962 | -0.2663 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.016 | -0.1828 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.846 | -0.1412 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1532 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7436 | +0.0113 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7416 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3941 | +0.0076 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.9018 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5044 | +0.00904 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.9099 | +0.03074 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.63 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5694e+05 | -6082 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8706e+05 | -2419 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.3 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5007e+05 | -3681 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.167 | -10.71 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.66619 | +0.08632 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66577 | +0.08618 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63908 | +0.08112 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.4781 | +0.05394 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.61891 | +0.05158 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61698 | +0.05124 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50949 | +0.03623 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.2564 | +0.01173 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.6374 | +0.06501 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63654 | +0.06482 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58185 | +0.05591 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36169 | +0.02674 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.94367 | -1.459 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2053 | +0.01578 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2373 | +0.01699 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.751 | -0.1565 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.69 | -8.443 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.26 | -8.351 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051837 | -0.004973 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1634 | +0.01396 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1784 | +0.03343 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.822 | -0.2124 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.906 | +16.46 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.469 | -1.474 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039786 | -0.002202 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1655 | +0.01445 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1804 | +0.03551 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.82 | -0.2293 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.702 | +10.26 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.858 | -2.112 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.213 | +18.12 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1492 | +0.007887 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 23.214 | +22.59 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.4037 | +0.6031 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.239 | +30 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.7557 | +0.2952 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6667 | +0.03851 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.4286 | +2.44 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.5599 | +3.226 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 8.5039 | +4.127 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 9.8731 | +4.413 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.533e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6512 | +0.0001609 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 473.72 | +304.3 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -307.4 | -311.4 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -8.6237 | -7.85 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.8829 | +0.09114 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.4438 | +4.789 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.3335 | +4.935 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 7.2059 | +4.47 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 10.291 | +3.444 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.958e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +3.033e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 1245 | +1192 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.00885 | +0.00679 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -6.3649 | -6.04 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.072 | -0.02456 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 5.5663 | +3.767 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.5751 | +4.179 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 8.4219 | +4.62 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 9.6833 | +1.261 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +7.654e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6508 | +0.0001248 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 265.49 | +207.6 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -258.48 | -250.6 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -7.2553 | -6.72 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4271 | +3.719 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1333 | +1.092 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.516e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.4911 | +3.6 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.6465 | +1.13 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.128e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6298 | +3.746 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1423 | +1.136 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.156e-06 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.789 | -0.2622 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 975.11 | -22.47 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00059 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.095313 | +0.02529 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.816 | -0.2159 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 409.06 | -12.67 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6893 | +0.05251 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.81 | -0.237 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 635.83 | -17.43 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6895 | +0.0758 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 95.763 | +94.82 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 180.37 | +178.6 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 181.24 | +180.2 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.263 | +9.739 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6626 | -0.005655 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.6645 | -0.1998 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 10.811 | +1.392 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.6598 | +0.03533 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.5742 | -0.1741 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9313 | -0.0003844 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.6671 | +0.1285 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.5811 | -0.1783 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7376 | -0.0008931 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: PASS  (90 PASS, 0 WARN, 0 FAIL, 0 missing)
