# compare.py L2b: AFE/layout/sim/post against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27565 | -0.005721 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 972.5 | -25.17 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.0739 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.42 | -0.2654 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.742 | -0.1933 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.83 | -0.1557 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28376 | -0.004036 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 408.49 | -13.61 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6501 | -0.00013 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3234 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.977 | -0.2946 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.732 | -0.1618 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.858 | -0.1293 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.84 | -0.2135 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.84 | -0.2135 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24144 | -0.004439 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 634.4 | -19.1 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | -3e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0776 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.962 | -0.2662 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.016 | -0.182 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.847 | -0.1412 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1531 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7436 | +0.01129 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7415 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.394 | +0.007522 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.9018 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5044 | +0.009046 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.91 | +0.03077 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.63 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5688e+05 | -6138 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8705e+05 | -2437 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.31 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5004e+05 | -3705 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.167 | -10.71 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.66495 | +0.08508 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66451 | +0.08493 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63782 | +0.07986 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.477 | +0.05284 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.61748 | +0.05015 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61554 | +0.0498 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50822 | +0.03496 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.25562 | +0.01096 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.63605 | +0.06366 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63517 | +0.06346 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58053 | +0.05459 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36071 | +0.02575 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.94376 | -1.459 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2053 | +0.01578 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2373 | +0.01699 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.751 | -0.1565 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.688 | -8.441 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.26 | -8.351 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051824 | -0.004987 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1632 | +0.01382 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1783 | +0.03329 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.822 | -0.2124 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.916 | +16.45 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.47 | -1.475 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039765 | -0.002223 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1654 | +0.01429 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1803 | +0.03535 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.82 | -0.2293 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.712 | +10.25 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.86 | -2.114 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.192 | +18.1 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1494 | +0.0081 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 19.798 | +19.18 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.4737 | +0.6732 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.265 | +30.03 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.4634 | +0.002902 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6379 | +0.00974 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.5168 | +2.528 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.5378 | +3.204 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 8.5058 | +4.129 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 7.521 | +2.061 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.54e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6512 | +0.000161 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 220.35 | +50.89 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -315.07 | -319.1 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -8.3683 | -7.595 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.8466 | +0.0548 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.4639 | +4.809 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.4318 | +5.033 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 7.3302 | +4.595 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 8.258 | +1.411 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.963e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +3.383e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 256.89 | +203.6 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.00654 | +0.00448 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -6.9441 | -6.619 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0246 | -0.07202 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 5.5919 | +3.792 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.5815 | +4.186 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 8.5706 | +4.769 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 9.4654 | +1.043 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +7.961e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6508 | +0.0001405 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 272.14 | +214.2 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -253.63 | -245.8 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -7.7247 | -7.19 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4247 | +3.716 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1325 | +1.091 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.668e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.5139 | +3.622 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.8389 | +1.322 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.188e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6287 | +3.745 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1432 | +1.137 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.154e-06 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.789 | -0.2622 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 975.12 | -22.46 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00059 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.095322 | +0.02529 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.816 | -0.216 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 409.06 | -12.67 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6592 | +0.02248 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.81 | -0.2371 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 635.83 | -17.44 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6644 | +0.05072 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 95.807 | +94.87 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 181.66 | +179.9 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 181.24 | +180.2 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.265 | +9.74 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6626 | -0.005696 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.6645 | -0.1998 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 10.809 | +1.39 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.6048 | -0.01964 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.5699 | -0.1785 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9312 | -0.0004896 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.609 | +0.07043 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.5804 | -0.179 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7376 | -0.0009172 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: PASS  (90 PASS, 0 WARN, 0 FAIL, 0 missing)
