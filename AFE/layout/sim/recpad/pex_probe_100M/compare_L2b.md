# compare.py L2b: AFE/layout/sim/recpad/pex_probe_100M against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 59.819 | -0.238 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 59.819 | -0.238 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.27581 | -0.005559 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 972.69 | -24.98 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 1.0782 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.419 | -0.2656 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.739 | -0.1962 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.829 | -0.1568 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.842 | -0.1958 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 59.842 | -0.1958 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.28306 | -0.004731 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 408.63 | -13.48 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | -1e-05 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 1.3227 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 57.977 | -0.2947 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.734 | -0.1596 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.857 | -0.1304 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 59.838 | -0.2148 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 59.838 | -0.2148 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24146 | -0.004427 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 634.58 | -18.92 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 1.0773 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 58.961 | -0.2665 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.014 | -0.1843 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.845 | -0.1423 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1535 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7439 | +0.01158 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7418 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3943 | +0.007777 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.9021 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.5046 | +0.009241 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.9106 | +0.03139 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 436.62 | +359.7 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.5714e+05 | -5883 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 46.942 | -11.76 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 441.13 | +359.8 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8709e+05 | -2391 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 48.598 | -9.931 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 439.3 | +359.7 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5013e+05 | -3614 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 48.167 | -10.71 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.6662 | +0.08632 | 0.32 .. 0.68 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.66578 | +0.08619 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.63908 | +0.08112 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.4781 | +0.05394 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.61892 | +0.05159 | 0.32 .. 0.68 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.61699 | +0.05125 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.50949 | +0.03623 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.2564 | +0.01173 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.63741 | +0.06502 | 0.32 .. 0.68 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.63655 | +0.06483 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.58185 | +0.05591 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.36169 | +0.02674 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 0.94255 | -1.46 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.2052 | +0.01571 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2373 | +0.01701 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.75 | -0.1575 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -44.697 | -8.45 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -46.273 | -8.363 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.051755 | -0.005055 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1631 | +0.01368 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.1783 | +0.03329 | <= 1.19 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 59.821 | -0.2134 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -73.995 | +16.37 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -66.469 | -1.474 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.039623 | -0.002365 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1652 | +0.0141 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1802 | +0.0353 | <= 1.19 | PASS |
| amp_thd | typ | gain_db | 60.049 | 59.819 | -0.2304 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -72.786 | +10.18 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -69.87 | -2.123 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 18.648 | +18.55 | <= 50 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1488 | +0.007557 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 20.518 | +19.9 | <= 50 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 1.6407 | -0.1599 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 30.636 | +30.4 | <= 50 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.5671 | +0.1066 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6359 | +0.007691 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 5.6835 | +2.695 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 5.6875 | +3.353 | <= 6.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 9.3063 | +4.929 | <= 9.75 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 10.103 | +4.643 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.672e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.6513 | +0.0002995 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 477.37 | +307.9 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | -338.22 | -342.3 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -12.247 | -11.47 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.8529 | +0.06117 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 5.6934 | +5.039 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 5.6971 | +5.299 | <= 6.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 8.6092 | +5.873 | <= 9.75 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 9.5997 | +2.752 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -2.042e-05 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6503 | +0.000102 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 722.5 | +669.2 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | -0.00019 | -0.00225 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -10.029 | -9.704 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0659 | -0.03067 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | nan |  | no value | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 9.9825 | +6.181 | <= 9.75 | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 12.078 | +3.655 | <= 12 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -5.491e-07 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6511 | +0.0004809 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 842.65 | +784.7 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -262.33 | -254.5 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -5.8191 | -5.284 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 7.4092 | +3.701 | <= 9.75 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 9.1243 | +1.083 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.917e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 6.4971 | +3.606 | <= 9.75 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 7.7507 | +1.234 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -5.071e-06 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 7.6189 | +3.735 | <= 9.75 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 9.1329 | +1.126 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -4.32e-06 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 59.788 | -0.2633 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 975.51 | -22.07 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6511 | -0.0006 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.095463 | +0.02544 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 59.813 | -0.219 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 408.84 | -12.89 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.1645 | -0.4722 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 59.806 | -0.2405 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 636.56 | -16.71 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.307 | -0.3067 | 1.5 .. 1.8 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 96.495 | +95.55 |  |  |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 166.78 | +165 |  |  |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 182 | +181 |  |  |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 11.326 | +9.802 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6619 | -0.006373 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.6641 | -0.2002 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 10.749 | +1.33 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 7.6165 | -1.008 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.5557 | -0.1927 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9312 | -0.0004969 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 8.6379 | -0.9006 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.5681 | -0.1913 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7372 | -0.00134 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: FAIL  (84 PASS, 0 WARN, 6 FAIL, 0 missing)
