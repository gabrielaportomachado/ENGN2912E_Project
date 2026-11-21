# compare.py L2b: AFE/layout/sim/post against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.237 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.237 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27565 | -0.005723 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 972.54 | -25.13 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.0764 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.42 | -0.2653 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.742 | -0.1933 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.83 | -0.1557 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28317 | -0.004624 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 408.51 | -13.6 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6501 | -9e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3274 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.977 | -0.2945 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.736 | -0.1582 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.858 | -0.1293 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.2414 | -0.004487 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 634.45 | -19.05 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0806 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.962 | -0.2661 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.016 | -0.182 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.847 | -0.1412 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1532 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7436 | +0.0113 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7416 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3941 | +0.007589 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.9018 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5044 | +0.00905 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.91 | +0.03078 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.63 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5688e+05 | -6135 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.954 | -11.75 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8705e+05 | -2436 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.61 | -9.919 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.31 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5004e+05 | -3704 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.179 | -10.7 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.66439 | +0.08451 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66396 | +0.08437 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63732 | +0.07936 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.47665 | +0.05248 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.61701 | +0.04967 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61507 | +0.04933 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50788 | +0.03462 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.25547 | +0.01081 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.63554 | +0.06315 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63467 | +0.06296 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.5801 | +0.05417 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36047 | +0.02551 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.93193 | -1.471 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2057 | +0.0162 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2375 | +0.01715 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.752 | -0.1559 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.793 | -8.545 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.371 | -8.462 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.052089 | -0.004721 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1635 | +0.01404 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1785 | +0.03348 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.822 | -0.2124 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.791 | +16.57 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.44 | -1.446 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.04006 | -0.001928 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1656 | +0.01453 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1805 | +0.03556 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.82 | -0.2294 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.611 | +10.35 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.817 | -2.07 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.465 | +18.37 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1493 | +0.008011 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 20.126 | +19.51 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.4733 | +0.6727 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.536 | +30.3 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.6814 | +0.2209 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6882 | +0.06003 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.5264 | +2.538 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.4563 | +3.122 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 8.6237 | +4.247 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 9.6824 | +4.222 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.54e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6512 | +0.000176 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 304.26 | +134.8 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -294.75 | -298.8 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -9.2586 | -8.485 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.997 | +0.2053 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.4077 | +4.753 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.4639 | +5.065 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 7.3566 | +4.621 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 8.4146 | +1.567 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.963e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +3.461e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 311.17 | +257.8 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | -53.685 | -53.69 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -7.0418 | -6.717 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 2.9882 | -0.1083 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 5.5885 | +3.789 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.5971 | +4.201 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 8.5088 | +4.707 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 9.8292 | +1.407 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +7.783e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6508 | +0.0001336 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 284.49 | +226.6 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -194.31 | -186.4 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -7.503 | -6.968 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.433 | +3.725 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1376 | +1.096 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.673e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.5109 | +3.619 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.5206 | +1.004 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.197e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6355 | +3.751 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1473 | +1.141 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.159e-06 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.789 | -0.2622 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 975.15 | -22.43 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00058 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.09532 | +0.02529 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.817 | -0.2159 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 409.07 | -12.66 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6592 | +0.02248 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.81 | -0.237 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 635.84 | -17.42 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6644 | +0.05072 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 96.401 | +95.46 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 180.07 | +178.3 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 182.56 | +181.5 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.332 | +9.807 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6626 | -0.005647 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.6645 | -0.1998 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 10.813 | +1.394 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.6137 | -0.01078 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.568 | -0.1803 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9315 | -0.0002426 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.6097 | +0.07115 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.5791 | -0.1803 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7376 | -0.0009169 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: PASS  (90 PASS, 0 WARN, 0 FAIL, 0 missing)
