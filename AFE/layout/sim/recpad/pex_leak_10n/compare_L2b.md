# compare.py L2b: AFE/layout/sim/recpad/pex_leak_10n against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.82 | -0.2369 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27566 | -0.005707 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 972.5 | -25.17 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.82 | +0.01 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.0747 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.42 | -0.2654 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.742 | -0.1934 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.83 | -0.1557 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.844 | -0.1945 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28324 | -0.004556 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 408.49 | -13.61 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.143 | +0.01 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6501 | -0.00012 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3236 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.977 | -0.2947 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.735 | -0.1586 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.858 | -0.1293 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.839 | -0.2138 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.2414 | -0.004489 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 634.43 | -19.07 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.44 | +0.01 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0775 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.962 | -0.2663 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.016 | -0.182 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.846 | -0.1412 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1531 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7435 | +0.01126 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7416 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3941 | +0.0076 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.9018 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5044 | +0.00905 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.91 | +0.03078 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.63 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5694e+05 | -6082 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8706e+05 | -2419 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.3 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5007e+05 | -3681 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.168 | -10.71 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.66619 | +0.08631 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66577 | +0.08618 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63908 | +0.08112 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.4781 | +0.05394 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.6189 | +0.05157 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61698 | +0.05124 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50949 | +0.03623 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.2564 | +0.01173 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.6374 | +0.06501 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63654 | +0.06482 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58185 | +0.05591 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36169 | +0.02674 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.94365 | -1.459 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2053 | +0.01578 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2373 | +0.01699 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.751 | -0.1565 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.69 | -8.442 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.261 | -8.352 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051881 | -0.00493 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1635 | +0.01409 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1785 | +0.03355 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.822 | -0.2124 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.858 | +16.51 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.469 | -1.474 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039835 | -0.002153 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1655 | +0.01442 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1804 | +0.03548 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.82 | -0.2294 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.653 | +10.31 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.867 | -2.121 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.092 | +18 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1493 | +0.008044 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 19.704 | +19.08 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 2.8054 | +1.005 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.06 | +29.82 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.7374 | +0.2769 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6606 | +0.03245 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 4.4707 | +1.482 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 4.6101 | +2.276 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 2.9334 | -1.443 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 7.3777 | +1.917 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.455e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.651 | -1.394e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 323.51 | +154 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -291.32 | -295.4 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -0.50764 | +0.2661 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.8826 | +0.09085 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 3.0858 | +2.431 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 2.88 | +2.482 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 1.6081 | -1.128 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 6.1275 | -0.7198 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -2.408e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | -6.351e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 235.09 | +181.8 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.00294 | +0.00088 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | 0.30854 | +0.6333 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0615 | -0.03511 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 4.8268 | +3.027 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 5.001 | +3.605 | <= 6.75 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 5.8903 | +2.089 | <= 9.75 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 7.2175 | -1.205 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +1.419e-06 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6506 | -3.808e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 222.28 | +164.3 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -254.11 | -246.2 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | 0.919 | +1.454 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4342 | +3.726 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1385 | +1.097 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.967e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.5025 | +3.611 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.6506 | +1.134 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -3.721e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6351 | +3.751 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1485 | +1.142 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -2.489e-06 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.789 | -0.2622 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 975.12 | -22.47 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.00058 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.095239 | +0.02521 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.816 | -0.2162 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 408.99 | -12.74 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.9594 | +0.3227 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.81 | -0.2364 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 636.16 | -17.11 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.9048 | +0.2911 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 95.563 | +94.62 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 179.97 | +178.2 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 180.83 | +179.8 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.233 | +9.709 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.663 | -0.005286 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.6648 | -0.1996 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 10.843 | +1.424 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 9.2049 | +0.5804 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.5816 | -0.1667 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9313 | -0.000441 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 10.193 | +0.6548 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.5877 | -0.1717 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7378 | -0.0006777 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: FAIL  (88 PASS, 0 WARN, 2 FAIL, 0 missing)
