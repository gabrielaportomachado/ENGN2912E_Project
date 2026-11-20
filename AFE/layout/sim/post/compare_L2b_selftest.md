# compare.py L2b: baseline (selftest) against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 60.057 | 60.057 | +0 | 59 .. 61 | PASS |
| amp_ac | ff85 | g_mid_db | 60.057 | 60.057 | +0 | |change| <= 0.3 | PASS |
| amp_ac | ff85 | f_lo_hz | 0.28137 | 0.28137 | +0 | <= 0.5 | PASS |
| amp_ac | ff85 | f_hi_hz | 997.67 | 997.67 | +0 | >= 300 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | ff85 | hf_dev_db | - | 0 |  | <= 2 | PASS |
| amp_ac | ff85 | g_300_db | 59.685 | 59.685 | +0 |  |  |
| amp_ac | ff85 | g_0p5_db | 58.936 | 58.936 | +0 |  |  |
| amp_ac | ff85 | g1_mid_db | 39.986 | 39.986 | +0 |  |  |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.038 | +0 | 59 .. 61 | PASS |
| amp_ac | ss-40 | g_mid_db | 60.038 | 60.038 | +0 | |change| <= 0.3 | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.2878 | 0.2878 | +0 | <= 0.5 | PASS |
| amp_ac | ss-40 | f_hi_hz | 422.1 | 422.1 | +0 | >= 300 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | ss-40 | vout_v | 1.6502 | 1.6502 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | ss-40 | hf_dev_db | - | 0 |  | <= 2 | PASS |
| amp_ac | ss-40 | g_300_db | 58.271 | 58.271 | +0 |  |  |
| amp_ac | ss-40 | g_0p5_db | 58.894 | 58.894 | +0 |  |  |
| amp_ac | ss-40 | g1_mid_db | 39.988 | 39.988 | +0 |  |  |
| amp_ac | typ | g_mid_db | 60.053 | 60.053 | +0 | 59 .. 61 | PASS |
| amp_ac | typ | g_mid_db | 60.053 | 60.053 | +0 | |change| <= 0.3 | PASS |
| amp_ac | typ | f_lo_hz | 0.24588 | 0.24588 | +0 | <= 0.5 | PASS |
| amp_ac | typ | f_hi_hz | 653.5 | 653.5 | +0 | >= 300 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | +0 | x / baseline 0.95 .. 1.05 | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac | typ | hf_dev_db | - | 0 |  | <= 2 | PASS |
| amp_ac | typ | g_300_db | 59.228 | 59.228 | +0 |  |  |
| amp_ac | typ | g_0p5_db | 59.198 | 59.198 | +0 |  |  |
| amp_ac | typ | g1_mid_db | 39.988 | 39.988 | +0 |  |  |
| amp_noise | ff85 | noise_d8_post_uv | - | 2.1392 |  | <= 2.2 | PASS |
| amp_noise | ff85 | noise_real_uv | 1.7323 | 1.7323 | +0 |  |  |
| amp_noise | ss-40 | noise_d8_post_uv | - | 1.7321 |  | <= 2 | PASS |
| amp_noise | ss-40 | noise_real_uv | 1.3865 | 1.3865 | +0 |  |  |
| amp_noise | typ | noise_d8_post_uv | - | 1.8904 |  | <= 2 | PASS |
| amp_noise | typ | noise_real_uv | 1.4954 | 1.4954 | +0 |  |  |
| amp_noise | typ | noise_real_fn1_uv | 4.8792 | 4.8792 | +0 |  |  |
| amp_loop | ff85 | pm_deg | 76.935 | 76.935 | +0 | >= 60 | PASS |
| amp_loop | ff85 | fu_hz | 3.6302e+05 | 3.6302e+05 | +0 |  |  |
| amp_loop | ff85 | t_100hz_db | 58.701 | 58.701 | +0 |  |  |
| amp_loop | ss-40 | pm_deg | 81.375 | 81.375 | +0 | >= 60 | PASS |
| amp_loop | ss-40 | fu_hz | 1.8948e+05 | 1.8948e+05 | +0 |  |  |
| amp_loop | ss-40 | t_100hz_db | 58.529 | 58.529 | +0 |  |  |
| amp_loop | typ | pm_deg | 79.573 | 79.573 | +0 | >= 60 | PASS |
| amp_loop | typ | fu_hz | 2.5375e+05 | 2.5375e+05 | +0 |  |  |
| amp_loop | typ | t_100hz_db | 58.878 | 58.878 | +0 |  |  |
| amp_psrr | ff85 | supply_gain_50hz | 0.57988 | 0.57988 | +0 | 0.38 .. 0.62 | PASS |
| amp_psrr | ff85 | supply_gain_60hz | 0.57959 | 0.57959 | +0 |  |  |
| amp_psrr | ff85 | supply_gain_300hz | 0.55796 | 0.55796 | +0 |  |  |
| amp_psrr | ff85 | supply_gain_1khz | 0.42417 | 0.42417 | +0 |  |  |
| amp_psrr | ss-40 | supply_gain_50hz | 0.56733 | 0.56733 | +0 | 0.38 .. 0.62 | PASS |
| amp_psrr | ss-40 | supply_gain_60hz | 0.56574 | 0.56574 | +0 |  |  |
| amp_psrr | ss-40 | supply_gain_300hz | 0.47326 | 0.47326 | +0 |  |  |
| amp_psrr | ss-40 | supply_gain_1khz | 0.24466 | 0.24466 | +0 |  |  |
| amp_psrr | typ | supply_gain_50hz | 0.57239 | 0.57239 | +0 | 0.38 .. 0.62 | PASS |
| amp_psrr | typ | supply_gain_60hz | 0.57172 | 0.57172 | +0 |  |  |
| amp_psrr | typ | supply_gain_300hz | 0.52594 | 0.52594 | +0 |  |  |
| amp_psrr | typ | supply_gain_1khz | 0.33496 | 0.33496 | +0 |  |  |
| amp_thd | ff85 | thd_pct | 2.4027 | 2.4027 | +0 | <= 4.5 | PASS |
| amp_thd | ff85 | out_max_v | 2.1895 | 2.1895 | +0 | >= 2.13 | PASS |
| amp_thd | ff85 | out_min_v | 1.2203 | 1.2203 | +0 | <= 1.25 | PASS |
| amp_thd | ff85 | gain_db | 59.908 | 59.908 | +0 | 58.8 .. 61 | PASS |
| amp_thd | ff85 | hd2_dbc | -36.248 | -36.248 | +0 |  |  |
| amp_thd | ff85 | hd3_dbc | -37.909 | -37.909 | +0 |  |  |
| amp_thd | ss-40 | thd_pct | 0.056811 | 0.056811 | +0 | <= 0.5 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1494 | 2.1494 | +0 | >= 2.13 | PASS |
| amp_thd | ss-40 | out_min_v | 1.145 | 1.145 | +0 | <= 1.17 | PASS |
| amp_thd | ss-40 | gain_db | 60.034 | 60.034 | +0 | 58.8 .. 61 | PASS |
| amp_thd | ss-40 | hd2_dbc | -90.366 | -90.366 | +0 |  |  |
| amp_thd | ss-40 | hd3_dbc | -64.995 | -64.995 | +0 |  |  |
| amp_thd | typ | thd_pct | 0.041988 | 0.041988 | +0 | <= 0.5 | PASS |
| amp_thd | typ | out_max_v | 2.1511 | 2.1511 | +0 | >= 2.13 | PASS |
| amp_thd | typ | out_min_v | 1.1449 | 1.1449 | +0 | <= 1.17 | PASS |
| amp_thd | typ | gain_db | 60.049 | 60.049 | +0 | 58.8 .. 61 | PASS |
| amp_thd | typ | hd2_dbc | -82.962 | -82.962 | +0 |  |  |
| amp_thd | typ | hd3_dbc | -67.746 | -67.746 | +0 |  |  |
| amp_pwrup | ff85 | err_1s_mv | 0.09506 | 0.09506 | +0 | <= 10 | PASS |
| amp_pwrup | ff85 | vout_before_v | 1.1413 | 1.1413 | +0 |  |  |
| amp_pwrup | ss-40 | err_1s_mv | 0.61939 | 0.61939 | +0 | <= 10 | PASS |
| amp_pwrup | ss-40 | vout_before_v | 1.8006 | 1.8006 | +0 |  |  |
| amp_pwrup | typ | err_1s_mv | 0.23517 | 0.23517 | +0 | <= 10 | PASS |
| amp_pwrup | typ | vout_before_v | 2.4605 | 2.4605 | +0 |  |  |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6282 | 1.6282 | +0 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 2.9885 | 2.9885 | +0 | <= 4.5 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 2.3341 | 2.3341 | +0 | <= 4.5 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 4.3769 | 4.3769 | +0 | <= 6.5 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 5.4605 | 5.4605 | +0 | <= 12 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.651 | 1.651 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset | ff85 | peak_mv_os100m | 169.46 | 169.46 | +0 |  |  |
| amp_reset | ff85 | rel_step_mv_os10m | 4.0326 | 4.0326 | +0 |  |  |
| amp_reset | ff85 | drift_mv_s_os10m | -0.77377 | -0.77377 | +0 |  |  |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.7918 | 5.7918 | +0 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 0.6545 | 0.6545 | +0 | <= 4.5 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 0.39849 | 0.39849 | +0 | <= 4.5 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 2.7357 | 2.7357 | +0 | <= 6.5 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 6.8473 | 6.8473 | +0 | <= 12 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset | ss-40 | peak_mv_os100m | 53.334 | 53.334 | +0 |  |  |
| amp_reset | ss-40 | rel_step_mv_os10m | 0.00206 | 0.00206 | +0 |  |  |
| amp_reset | ss-40 | drift_mv_s_os10m | -0.32478 | -0.32478 | +0 |  |  |
| amp_reset | typ | t_fs_ms_os10m | 3.0966 | 3.0966 | +0 | x / baseline 0.7 .. 1.4 | PASS |
| amp_reset | typ | t_1mv_s_os0 | 1.7995 | 1.7995 | +0 | <= 4.5 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 1.3957 | 1.3957 | +0 | <= 4.5 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 3.8016 | 3.8016 | +0 | <= 6.5 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 8.4225 | 8.4225 | +0 | <= 12 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | final_v_os10m | 1.6507 | 1.6507 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset | typ | peak_mv_os100m | 57.939 | 57.939 | +0 |  |  |
| amp_reset | typ | rel_step_mv_os10m | -7.8744 | -7.8744 | +0 |  |  |
| amp_reset | typ | drift_mv_s_os10m | -0.53498 | -0.53498 | +0 |  |  |
| amp_reset_host | ff85 | t_1mv_s_os10m | 3.7084 | 3.7084 | +0 | <= 6.5 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 8.0417 | 8.0417 | +0 | <= 12 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 2.8915 | 2.8915 | +0 | <= 6.5 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 6.5169 | 6.5169 | +0 | <= 12 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | +0 | 1.6 .. 1.7 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 3.8841 | 3.8841 | +0 | <= 6.5 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 8.0065 | 8.0065 | +0 | <= 12 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | +0 | 1.6 .. 1.7 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 60.051 | 60.051 | +0 | 59 .. 61 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 997.59 | 997.59 | +0 | >= 300 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6517 | 1.6517 | +0 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.070028 | 0.070028 | +0 | <= 0.5 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 60.032 | 60.032 | +0 | 59 .. 61 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 421.73 | 421.73 | +0 | >= 300 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6367 | 1.6367 | +0 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_ac_junction | typ | g_mid_db | 60.047 | 60.047 | +0 | 59 .. 61 | PASS |
| amp_ac_junction | typ | f_hi_hz | 653.27 | 653.27 | +0 | >= 300 | PASS |
| amp_ac_junction | typ | vout_v | 1.6137 | 1.6137 | +0 | 1.5 .. 1.8 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan |  | nan allowed | PASS |
| amp_pwrup_junction | ff85 | err_1s_mv | 0.94002 | 0.94002 | +0 | <= 50 | PASS |
| amp_pwrup_junction | ss-40 | err_1s_mv | 1.749 | 1.749 | +0 | <= 50 | PASS |
| amp_pwrup_junction | typ | err_1s_mv | 1.0352 | 1.0352 | +0 | <= 50 | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 1.5242 | 1.5242 | +0 | |x| <= 30 | PASS |
| amp_reset_host_junction | ff85 | final_v_os10m | 1.6683 | 1.6683 | +0 |  |  |
| amp_reset_host_junction | ff85 | final_v_os100m | 1.8643 | 1.8643 | +0 |  |  |
| amp_reset_host_junction | ff85 | t_1mv_s_os10m | 9.419 | 9.419 | +0 |  |  |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6245 | 8.6245 | +0 | |x| <= 30 | PASS |
| amp_reset_host_junction | ss-40 | final_v_os10m | 1.7484 | 1.7484 | +0 |  |  |
| amp_reset_host_junction | ss-40 | final_v_os100m | 2.9317 | 2.9317 | +0 |  |  |
| amp_reset_host_junction | ss-40 | t_1mv_s_os10m | nan | nan |  |  |  |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.5386 | 9.5386 | +0 | |x| <= 30 | PASS |
| amp_reset_host_junction | typ | final_v_os10m | 1.7594 | 1.7594 | +0 |  |  |
| amp_reset_host_junction | typ | final_v_os100m | 2.7385 | 2.7385 | +0 |  |  |
| amp_reset_host_junction | typ | t_1mv_s_os10m | nan | nan |  |  |  |

RESULT compare L2b: PASS  (93 PASS, 0 WARN, 0 FAIL, 0 missing)
