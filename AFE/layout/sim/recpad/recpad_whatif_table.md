# R13 recpad_table.md (written by mk_tables.py; limits = AFE/layout/accept_limits.json, Decision 51)

| case | rows with a limit | with the pad | without the pad | compare.py verdict |
|---|---|---|---|---|
| pex_probe_1G | 87 | 87 PASS / 0 WARN / 0 FAIL | 0 FAIL | PASS |
| pex_probe_100M | 87 | 81 PASS / 0 WARN / 6 FAIL | 0 FAIL | FAIL |
| pex_probe_ac | 87 | 65 PASS / 1 WARN / 21 FAIL | 0 FAIL | FAIL |
| pex_probe_rs100k | 87 | 74 PASS / 0 WARN / 13 FAIL | 0 FAIL | FAIL |
| pex_leak_1n | 87 | 87 PASS / 0 WARN / 0 FAIL | 0 FAIL | PASS |
| pex_leak_10n | 87 | 85 PASS / 0 WARN / 2 FAIL | 0 FAIL | FAIL |
| pex_ctl_1f | 33 | 33 PASS / 0 WARN / 0 FAIL | 0 FAIL | FAIL |
| pex_check_nodiodes | 33 | 32 PASS / 0 WARN / 1 FAIL | 0 FAIL | FAIL |

## pex_probe_1G

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.82 | -0.00020027 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.2757 | 5.0906e-05 | <= 0.5 | 0.22435 | 0.2243 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 972.51 | 0.0025542 | >= 300 | 672.5 | 672.51 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | 0.04903 | 0.04904 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.079 | 0.0050979 | <= 2 | 0.92608 | 0.92099 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.843 | -0.00042091 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.28301 | -0.00074971 | <= 0.5 | 0.21624 | 0.21699 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 408.64 | 0.1415 | >= 300 | 108.49 | 108.64 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6502 | 0.00015 | 1.6 .. 1.7 | 0.04993 | 0.04978 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.3215 | -0.0019827 | <= 2 | 0.67657 | 0.67855 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.839 | -0.0004539 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.2414 | -4.4255e-05 | <= 0.5 | 0.25856 | 0.2586 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 634.44 | 0.033061 | >= 300 | 334.4 | 334.44 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 4e-05 | 1.6 .. 1.7 | 0.0494 | 0.04936 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.0781 | 0.0005054 | <= 2 | 0.92239 | 0.92188 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.1532 | 8.7402e-05 | <= 2.2 | 0.046855 | 0.046767 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7416 | 0.00015113 | <= 2 | 0.25853 | 0.25838 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.9019 | 4.895e-05 | <= 2 | 0.098172 | 0.098123 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.62 | -0.013 | >= 60 | 376.63 | 376.62 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.003 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.3 | -0.005 | >= 60 | 379.31 | 379.3 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.6662 | 0.001243 | 0.32 .. 0.68 | 0.015047 | 0.013804 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.6189 | 0.00142 | 0.32 .. 0.68 | 0.062521 | 0.061101 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.6374 | 0.001351 | 0.32 .. 0.68 | 0.043949 | 0.042598 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.94358 | -0.00017697 | <= 4.5 | 3.5562 | 3.5564 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2053 | -1.805e-05 | >= 2.13 | 0.075295 | 0.075277 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2373 | 2.6e-06 | <= 1.25 | 0.01271 | 0.012707 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.751 | -0.00020009 | 58.8 .. 61 | 0.95109 | 0.95089 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051813 | -1.0792e-05 | <= 0.5 | 0.44818 | 0.44819 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1632 | -8.826e-05 | >= 2.13 | 0.033241 | 0.033153 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.1782 | -6.211e-05 | <= 1.19 | 0.011732 | 0.011794 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.822 | -0.00020424 | 58.8 .. 61 | 1.0218 | 1.0216 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039761 | -3.9849e-06 | <= 0.5 | 0.46023 | 0.46024 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1654 | 1.038e-05 | >= 2.13 | 0.035369 | 0.035379 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1803 | 3.479e-05 | <= 1.19 | 0.009744 | 0.0097093 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.82 | -0.00019861 | 58.8 .. 61 | 1.0201 | 1.0199 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 18.414 | 0.22156 | <= 50 | 31.808 | 31.586 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 19.789 | -0.00862 | <= 50 | 30.202 | 30.211 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 30.31 | 0.04433 | <= 50 | 19.735 | 19.69 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6738 | 0.035894 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.4819 | -0.034881 | <= 6.75 | 1.2332 | 1.2681 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.5449 | 0.0070522 | <= 6.75 | 1.2122 | 1.2051 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 8.7922 | 0.28639 | <= 9.75 | 1.2442 | 0.95778 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 7.0662 | -0.45481 | <= 12 | 4.479 | 4.9338 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -3.0605e-08 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6512 | 3.9285e-05 | 1.6 .. 1.7 | 0.048847 | 0.048807 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.9532 | 0.10664 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 5.4631 | -0.00072416 | <= 6.75 | 1.2861 | 1.2869 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | 5.5081 | 0.076314 | <= 6.75 | 1.3182 | 1.2419 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 7.4792 | 0.14891 | <= 9.75 | 2.4198 | 2.2708 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 8.595 | 0.33692 | <= 12 | 3.742 | 3.405 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -7.2805e-08 | 1.6 .. 1.7 | 0.049736 | 0.049736 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | 4.7209e-06 | 1.6 .. 1.7 | 0.049757 | 0.049752 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0662 | 0.041657 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | 5.6247 | 0.032764 | <= 6.75 | 1.1581 | 1.1253 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | 5.6238 | 0.042303 | <= 6.75 | 1.1685 | 1.1262 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 8.7861 | 0.21546 | <= 9.75 | 1.1794 | 0.96393 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 9.9141 | 0.44874 | <= 12 | 2.5346 | 2.0859 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -2.6848e-07 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6508 | 2.6857e-05 | 1.6 .. 1.7 | 0.049201 | 0.049174 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.4247 | -2.961e-05 | <= 9.75 | 2.3253 | 2.3253 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.1319 | -0.00062288 | <= 12 | 2.8675 | 2.8681 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -8.0742e-09 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.4757 | -0.0382 | <= 9.75 | 3.2361 | 3.2743 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.5065 | -0.33235 | <= 12 | 4.1611 | 4.4935 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.0124e-07 | 1.6 .. 1.7 | 0.049737 | 0.049737 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.6288 | 7.498e-05 | <= 9.75 | 2.1213 | 2.1212 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.1424 | -0.00081295 | <= 12 | 2.8568 | 2.8576 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -1.5989e-07 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.789 | -0.00020117 | 59 .. 61 | 0.78902 | 0.78882 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 975.13 | 0.0058893 | >= 300 | 675.12 | 675.13 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.6511 | 1e-05 | 1.5 .. 1.8 | 0.14886 | 0.14885 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.095335 | 1.3112e-05 | <= 0.5 | 0.40468 | 0.40467 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | 59.816 | -0.00031666 | 59 .. 61 | 0.81645 | 0.81613 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 409.05 | -0.0094301 | >= 300 | 109.06 | 109.05 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 1.6097 | -0.04954 | 1.5 .. 1.8 | 0.14077 | 0.10969 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_ac_junction | typ | g_mid_db | 59.81 | 59.809 | -0.00038546 | 59 .. 61 | 0.80975 | 0.80936 | PASS |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 635.81 | -0.015835 | >= 300 | 335.83 | 335.81 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 1.6232 | -0.04121 | 1.5 .. 1.8 | 0.13559 | 0.1232 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | 11.277 | 0.012107 | |x| <= 30 | 18.735 | 18.723 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | 8.5045 | -0.10035 | |x| <= 30 | 21.395 | 21.496 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | 9.511 | -0.098007 | |x| <= 30 | 20.391 | 20.489 | PASS |

## pex_probe_100M

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.819 | -0.0010741 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.27581 | 0.00016119 | <= 0.5 | 0.22435 | 0.22419 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 972.69 | 0.19121 | >= 300 | 672.5 | 672.69 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | 0.04903 | 0.04904 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.0782 | 0.0042619 | <= 2 | 0.92608 | 0.92182 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.842 | -0.0013103 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.28306 | -0.00069509 | <= 0.5 | 0.21624 | 0.21694 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 408.63 | 0.13487 | >= 300 | 108.49 | 108.63 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6502 | 0.00012 | 1.6 .. 1.7 | 0.04993 | 0.04981 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.3227 | -0.00073897 | <= 2 | 0.67657 | 0.67731 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.838 | -0.0013323 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.24146 | 1.1843e-05 | <= 0.5 | 0.25856 | 0.25854 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 634.58 | 0.1733 | >= 300 | 334.4 | 334.58 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 3e-05 | 1.6 .. 1.7 | 0.0494 | 0.04937 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.0773 | -0.0003343 | <= 2 | 0.92239 | 0.92272 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.1535 | 0.00036096 | <= 2.2 | 0.046855 | 0.046494 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7418 | 0.00031888 | <= 2 | 0.25853 | 0.25821 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.9021 | 0.00024603 | <= 2 | 0.098172 | 0.097926 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.62 | -0.013 | >= 60 | 376.63 | 376.62 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.003 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.3 | -0.005 | >= 60 | 379.31 | 379.3 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.6662 | 0.001248 | 0.32 .. 0.68 | 0.015047 | 0.013799 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.61892 | 0.001439 | 0.32 .. 0.68 | 0.062521 | 0.061082 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.63741 | 0.001359 | 0.32 .. 0.68 | 0.043949 | 0.04259 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.94255 | -0.0012096 | <= 4.5 | 3.5562 | 3.5574 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2052 | -7.598e-05 | >= 2.13 | 0.075295 | 0.075219 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2373 | 2.18e-05 | <= 1.25 | 0.01271 | 0.012688 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.75 | -0.0010005 | 58.8 .. 61 | 0.95109 | 0.95009 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051755 | -6.8339e-05 | <= 0.5 | 0.44818 | 0.44824 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1631 | -0.00014658 | >= 2.13 | 0.033241 | 0.033095 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.1783 | -2.58e-06 | <= 1.19 | 0.011732 | 0.011734 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.821 | -0.001084 | 58.8 .. 61 | 1.0218 | 1.0207 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039623 | -0.00014195 | <= 0.5 | 0.46023 | 0.46038 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1652 | -0.00019022 | >= 2.13 | 0.035369 | 0.035179 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1802 | -5.124e-05 | <= 1.19 | 0.009744 | 0.0097953 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.819 | -0.001091 | 58.8 .. 61 | 1.0201 | 1.019 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 18.648 | 0.45603 | <= 50 | 31.808 | 31.352 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 20.518 | 0.71991 | <= 50 | 30.202 | 29.482 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 30.636 | 0.37087 | <= 50 | 19.735 | 19.364 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6359 | -0.002049 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.6835 | 0.16673 | <= 6.75 | 1.2332 | 1.0665 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.6875 | 0.14962 | <= 6.75 | 1.2122 | 1.0625 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 9.3063 | 0.80048 | <= 9.75 | 1.2442 | 0.44368 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 10.103 | 2.5822 | <= 12 | 4.479 | 1.8968 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.3197e-06 | 1.6 .. 1.7 | 0.048911 | 0.048912 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6513 | 0.00013849 | 1.6 .. 1.7 | 0.048847 | 0.048708 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.8529 | 0.00637 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 5.6934 | 0.22958 | <= 6.75 | 1.2861 | 1.0566 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | 5.6971 | 0.26522 | <= 6.75 | 1.3182 | 1.0529 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 8.6092 | 1.2789 | <= 9.75 | 2.4198 | 1.1408 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 9.5997 | 1.3417 | <= 12 | 3.742 | 2.4003 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -7.9989e-07 | 1.6 .. 1.7 | 0.049736 | 0.049737 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6503 | 6.8185e-05 | 1.6 .. 1.7 | 0.049757 | 0.049689 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0659 | 0.04135 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 9.9825 | 1.4118 | <= 9.75 | 1.1794 | -0.23246 | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 12.078 | 2.6124 | <= 12 | 2.5346 | -0.077766 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -1.3452e-06 | 1.6 .. 1.7 | 0.049257 | 0.049258 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6511 | 0.00034043 | 1.6 .. 1.7 | 0.049201 | 0.04886 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.4092 | -0.015456 | <= 9.75 | 2.3253 | 2.3408 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.1243 | -0.0081798 | <= 12 | 2.8675 | 2.8757 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.2491e-06 | 1.6 .. 1.7 | 0.048911 | 0.048912 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.4971 | -0.0168 | <= 9.75 | 3.2361 | 3.2529 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.7507 | -0.088182 | <= 12 | 4.1611 | 4.2493 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -8.8288e-07 | 1.6 .. 1.7 | 0.049737 | 0.049737 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.6189 | -0.0098055 | <= 9.75 | 2.1213 | 2.1311 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.1329 | -0.010348 | <= 12 | 2.8568 | 2.8671 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -1.1662e-06 | 1.6 .. 1.7 | 0.049257 | 0.049258 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.788 | -0.0010579 | 59 .. 61 | 0.78902 | 0.78796 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 975.51 | 0.39307 | >= 300 | 675.12 | 675.51 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.6511 | -1e-05 | 1.5 .. 1.8 | 0.14886 | 0.14887 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.095463 | 0.00014109 | <= 0.5 | 0.40468 | 0.40454 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | 59.813 | -0.0030332 | 59 .. 61 | 0.81645 | 0.81341 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 408.84 | -0.22366 | >= 300 | 109.06 | 108.84 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 1.1645 | -0.49471 | 1.5 .. 1.8 | 0.14077 | -0.33548 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_ac_junction | typ | g_mid_db | 59.81 | 59.806 | -0.0034112 | 59 .. 61 | 0.80975 | 0.80634 | PASS |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 636.56 | 0.73211 | >= 300 | 335.83 | 336.56 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 1.307 | -0.35737 | 1.5 .. 1.8 | 0.13559 | -0.19296 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | 11.326 | 0.061494 | |x| <= 30 | 18.735 | 18.674 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | 7.6165 | -0.98829 | |x| <= 30 | 21.395 | 22.383 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | 8.6379 | -0.97105 | |x| <= 30 | 20.391 | 21.362 | PASS |

## pex_probe_ac

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.811 | -0.0096734 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.27639 | 0.00073991 | <= 0.5 | 0.22435 | 0.22361 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 973.98 | 1.4815 | >= 300 | 672.5 | 673.98 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.6509 | -2e-05 | 1.6 .. 1.7 | 0.04903 | 0.04905 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.07 | -0.0039393 | <= 2 | 0.92608 | 0.93002 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.833 | -0.010214 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.28342 | -0.00033822 | <= 0.5 | 0.21624 | 0.21658 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 409.39 | 0.8935 | >= 300 | 108.49 | 109.39 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6502 | 0.00013 | 1.6 .. 1.7 | 0.04993 | 0.0498 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.3146 | -0.0088235 | <= 2 | 0.67657 | 0.68539 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.83 | -0.00998 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.24193 | 0.00048971 | <= 0.5 | 0.25856 | 0.25807 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 635.57 | 1.1631 | >= 300 | 334.4 | 335.57 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 2e-05 | 1.6 .. 1.7 | 0.0494 | 0.04938 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.069 | -0.0085906 | <= 2 | 0.92239 | 0.93098 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.1556 | 0.0024437 | <= 2.2 | 0.046855 | 0.044411 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7436 | 0.0021045 | <= 2 | 0.25853 | 0.25642 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.904 | 0.0021779 | <= 2 | 0.098172 | 0.095994 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.62 | -0.013 | >= 60 | 376.63 | 376.62 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.003 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.28 | -0.025 | >= 60 | 379.31 | 379.28 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.6662 | 0.001243 | 0.32 .. 0.68 | 0.015047 | 0.013804 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.6189 | 0.001424 | 0.32 .. 0.68 | 0.062521 | 0.061097 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.6374 | 0.001349 | 0.32 .. 0.68 | 0.043949 | 0.0426 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.93126 | -0.012501 | <= 4.5 | 3.5562 | 3.5687 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2046 | -0.00067805 | >= 2.13 | 0.075295 | 0.074617 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2375 | 0.00021344 | <= 1.25 | 0.01271 | 0.012497 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.742 | -0.0092712 | 58.8 .. 61 | 0.95109 | 0.94182 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051814 | -9.6149e-06 | <= 0.5 | 0.44818 | 0.44819 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1628 | -0.0004255 | >= 2.13 | 0.033241 | 0.032816 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.179 | 0.00070246 | <= 1.19 | 0.011732 | 0.011029 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.812 | -0.0099638 | 58.8 .. 61 | 1.0218 | 1.0118 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039706 | -5.9046e-05 | <= 0.5 | 0.46023 | 0.46029 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1648 | -0.0005324 | >= 2.13 | 0.035369 | 0.034837 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1809 | 0.00059763 | <= 1.19 | 0.009744 | 0.0091464 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.81 | -0.0099645 | 58.8 .. 61 | 1.0201 | 1.0101 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 891.71 | 873.52 | <= 50 | 31.808 | -841.71 | FAIL |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 441.75 | 421.95 | <= 50 | 30.202 | -391.75 | FAIL |
| amp_pwrup | typ | err_1s_mv | 30.265 | 1186.8 | 1156.5 | <= 50 | 19.735 | -1136.8 | FAIL |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6049 | -0.033008 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.5001 | -0.016681 | <= 6.75 | 1.2332 | 1.2499 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.4995 | -0.038367 | <= 6.75 | 1.2122 | 1.2505 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | nan | nan | no value | - | - | FAIL |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 37.412 | 29.891 | <= 12 | 4.479 | -25.412 | FAIL |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6504 | -0.00068605 | 1.6 .. 1.7 | 0.048911 | 0.049597 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.2864 | -0.36472 | 1.6 .. 1.7 | 0.048847 | -0.31357 | FAIL |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.8286 | -0.01792 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 10.396 | 3.0654 | <= 9.75 | 2.4198 | -0.64563 | FAIL |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 11.533 | 3.2746 | <= 12 | 3.742 | 0.46741 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -1.4968e-08 | 1.6 .. 1.7 | 0.049736 | 0.049736 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6495 | -0.00071021 | 1.6 .. 1.7 | 0.049757 | 0.049533 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0228 | -0.00174 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 11.387 | 2.8164 | <= 9.75 | 1.1794 | -1.637 | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 19.929 | 10.463 | <= 12 | 2.5346 | -7.9285 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | 3.433e-07 | 1.6 .. 1.7 | 0.049257 | 0.049256 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6457 | -0.0050666 | 1.6 .. 1.7 | 0.049201 | 0.045732 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 11.06 | 3.635 | <= 9.75 | 2.3253 | -1.3097 | FAIL |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | nan | nan | no value | - | - | FAIL |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.2958 | -0.35532 | 1.6 .. 1.7 | 0.048911 | -0.30423 | FAIL |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 10.716 | 4.2018 | <= 9.75 | 3.2361 | -0.9657 | FAIL |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 12.425 | 4.586 | <= 12 | 4.1611 | -0.42492 | FAIL |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | 4.6458e-08 | 1.6 .. 1.7 | 0.049737 | 0.049736 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 10.483 | 2.8545 | <= 9.75 | 2.1213 | -0.73325 | FAIL |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | nan | nan | no value | - | - | FAIL |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 0.81635 | -0.83439 | 1.6 .. 1.7 | 0.049257 | -0.78365 | FAIL |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.779 | -0.0099853 | 59 .. 61 | 0.78902 | 0.77903 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 977.34 | 2.2193 | >= 300 | 675.12 | 677.34 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.6511 | 1e-05 | 1.5 .. 1.8 | 0.14886 | 0.14885 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.095228 | -9.4196e-05 | <= 0.5 | 0.40468 | 0.40477 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | 59.806 | -0.009986 | 59 .. 61 | 0.81645 | 0.80646 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 409.01 | -0.055037 | >= 300 | 109.06 | 109.01 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 1.6592 | 0 | 1.5 .. 1.8 | 0.14077 | 0.14077 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_ac_junction | typ | g_mid_db | 59.81 | 59.8 | -0.0099857 | 59 .. 61 | 0.80975 | 0.79976 | PASS |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 635.75 | -0.079847 | >= 300 | 335.83 | 335.75 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 1.6644 | 0 | 1.5 .. 1.8 | 0.13559 | 0.13559 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | -253.6 | -264.87 | |x| <= 30 | 18.735 | -223.6 | WARN |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | 9.6848 | 1.08 | |x| <= 30 | 21.395 | 20.315 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | -28.458 | -38.067 | |x| <= 30 | 20.391 | 1.542 | PASS |

## pex_probe_rs100k

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.811 | -0.0095274 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.27737 | 0.001716 | <= 0.5 | 0.22435 | 0.22263 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 973.99 | 1.4832 | >= 300 | 672.5 | 673.99 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.6509 | -7e-05 | 1.6 .. 1.7 | 0.04903 | 0.0491 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.1007 | 0.026783 | <= 2 | 0.92608 | 0.8993 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.834 | -0.010011 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.28369 | -6.9606e-05 | <= 0.5 | 0.21624 | 0.21631 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 409.38 | 0.88424 | >= 300 | 108.49 | 109.38 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.133 | -0.0001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6502 | 0.00012 | 1.6 .. 1.7 | 0.04993 | 0.04981 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.331 | 0.0075574 | <= 2 | 0.67657 | 0.66901 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.83 | -0.010036 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.24205 | 0.0006006 | <= 0.5 | 0.25856 | 0.25795 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 635.59 | 1.1895 | >= 300 | 334.4 | 335.59 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.43 | -0.0001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 3e-05 | 1.6 .. 1.7 | 0.0494 | 0.04937 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.0851 | 0.0074808 | <= 2 | 0.92239 | 0.91491 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.1559 | 0.0027976 | <= 2.2 | 0.046855 | 0.044057 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7435 | 0.0020644 | <= 2 | 0.25853 | 0.25646 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.904 | 0.0021521 | <= 2 | 0.098172 | 0.09602 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.62 | -0.014 | >= 60 | 376.63 | 376.62 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.007 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.3 | -0.01 | >= 60 | 379.31 | 379.3 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.66601 | 0.001057 | 0.32 .. 0.68 | 0.015047 | 0.01399 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.61883 | 0.001353 | 0.32 .. 0.68 | 0.062521 | 0.061168 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.63722 | 0.001172 | 0.32 .. 0.68 | 0.043949 | 0.042777 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.93296 | -0.010803 | <= 4.5 | 3.5562 | 3.567 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2046 | -0.0007041 | >= 2.13 | 0.075295 | 0.074591 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2375 | 0.00019568 | <= 1.25 | 0.01271 | 0.012514 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.742 | -0.0090397 | 58.8 .. 61 | 0.95109 | 0.94205 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051244 | -0.00057963 | <= 0.5 | 0.44818 | 0.44876 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1608 | -0.0024344 | >= 2.13 | 0.033241 | 0.030807 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.1772 | -0.0011109 | <= 1.19 | 0.011732 | 0.012842 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.812 | -0.0098219 | 58.8 .. 61 | 1.0218 | 1.0119 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039225 | -0.00054062 | <= 0.5 | 0.46023 | 0.46078 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1633 | -0.0020832 | >= 2.13 | 0.035369 | 0.033286 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1794 | -0.00081728 | <= 1.19 | 0.009744 | 0.010561 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.81 | -0.0098263 | 58.8 .. 61 | 1.0201 | 1.0103 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 21.519 | 3.3271 | <= 50 | 31.808 | 28.481 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 22.739 | 2.9413 | <= 50 | 30.202 | 27.261 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 33.817 | 3.5519 | <= 50 | 19.735 | 16.183 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6853 | 0.047399 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.6959 | 0.17911 | <= 6.75 | 1.2332 | 1.0541 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.6816 | 0.14377 | <= 6.75 | 1.2122 | 1.0684 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 9.1942 | 0.68833 | <= 9.75 | 1.2442 | 0.55584 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 7.9855 | 0.46447 | <= 12 | 4.479 | 4.0145 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.2849e-05 | 1.6 .. 1.7 | 0.048911 | 0.048924 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6513 | 0.00010139 | 1.6 .. 1.7 | 0.048847 | 0.048745 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.8837 | 0.03709 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 5.2062 | -0.25764 | <= 6.75 | 1.2861 | 1.5438 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | nan | nan | no value | - | - | FAIL |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 11.99 | 4.6594 | <= 9.75 | 2.4198 | -2.2397 | FAIL |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 22.517 | 14.259 | <= 12 | 3.742 | -10.517 | FAIL |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -8.4446e-06 | 1.6 .. 1.7 | 0.049736 | 0.049745 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.8376 | 0.18735 | 1.6 .. 1.7 | 0.049757 | -0.13759 | FAIL |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0973 | 0.072765 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | nan | nan | no value | - | - | FAIL |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 16.381 | 6.9157 | <= 12 | 2.5346 | -4.3811 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -1.2084e-05 | 1.6 .. 1.7 | 0.049257 | 0.049269 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6761 | 0.025298 | 1.6 .. 1.7 | 0.049201 | 0.023903 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.2495 | -0.17519 | <= 9.75 | 2.3253 | 2.5005 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.0247 | -0.1078 | <= 12 | 2.8675 | 2.9753 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -1.259e-05 | 1.6 .. 1.7 | 0.048911 | 0.048924 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.3951 | -0.1188 | <= 9.75 | 3.2361 | 3.3549 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.59 | -0.24892 | <= 12 | 4.1611 | 4.41 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -8.4917e-06 | 1.6 .. 1.7 | 0.049737 | 0.049745 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.5023 | -0.12645 | <= 9.75 | 2.1213 | 2.2477 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.0391 | -0.10413 | <= 12 | 2.8568 | 2.9609 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -1.2166e-05 | 1.6 .. 1.7 | 0.049257 | 0.049269 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.78 | -0.0095154 | 59 .. 61 | 0.78902 | 0.7795 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 977.28 | 2.1632 | >= 300 | 675.12 | 677.28 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.651 | -0.00013 | 1.5 .. 1.8 | 0.14886 | 0.14899 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.097859 | 0.0025373 | <= 0.5 | 0.40468 | 0.40214 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | -1.8351 | -61.652 | 59 .. 61 | 0.81645 | -60.835 | FAIL |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 2.209e+05 | 2.2049e+05 | >= 300 | 109.06 | 2.206e+05 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 0.40201 | -1.2572 | 1.5 .. 1.8 | 0.14077 | -1.098 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | 10200 | nan | <= 0.5 | nan | -10199 | FAIL |
| amp_ac_junction | typ | g_mid_db | 59.81 | 29.05 | -30.76 | 59 .. 61 | 0.80975 | -29.95 | FAIL |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 9350.7 | 8714.9 | >= 300 | 335.83 | 9050.7 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 0.8046 | -0.85981 | 1.5 .. 1.8 | 0.13559 | -0.6954 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | 0.0025644 | nan | <= 0.5 | nan | 0.49744 | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | 11.809 | 0.54445 | |x| <= 30 | 18.735 | 18.191 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | -1.2112 | -9.816 | |x| <= 30 | 21.395 | 28.789 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | 0.071756 | -9.5372 | |x| <= 30 | 20.391 | 29.928 | PASS |

## pex_leak_1n

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.82 | -2.3325e-05 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.27565 | -2.036e-06 | <= 0.5 | 0.22435 | 0.22435 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 972.5 | -0.0041037 | >= 300 | 672.5 | 672.5 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.81 | 0.001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | 0.04903 | 0.04904 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.0747 | 0.00082405 | <= 2 | 0.92608 | 0.92526 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.843 | -0.00025232 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.28301 | -0.00075194 | <= 0.5 | 0.21624 | 0.21699 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 408.51 | 0.015652 | >= 300 | 108.49 | 108.51 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.134 | 0.001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6502 | 0.00013 | 1.6 .. 1.7 | 0.04993 | 0.0498 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.3234 | -7.779e-05 | <= 2 | 0.67657 | 0.67664 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.839 | -0.00026789 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.24155 | 0.00010201 | <= 0.5 | 0.25856 | 0.25845 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 634.43 | 0.027155 | >= 300 | 334.4 | 334.43 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.431 | 0.001 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6508 | 0.00016 | 1.6 .. 1.7 | 0.0494 | 0.04924 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.0775 | -9.3388e-05 | <= 2 | 0.92239 | 0.92248 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.1532 | 1.2607e-05 | <= 2.2 | 0.046855 | 0.046842 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7416 | 9.8309e-05 | <= 2 | 0.25853 | 0.25843 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.9018 | -7.7192e-06 | <= 2 | 0.098172 | 0.09818 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.63 | -0.003 | >= 60 | 376.63 | 376.63 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.001 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.3 | -0.002 | >= 60 | 379.31 | 379.3 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.66619 | 0.001242 | 0.32 .. 0.68 | 0.015047 | 0.013805 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.61891 | 0.001428 | 0.32 .. 0.68 | 0.062521 | 0.061093 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.6374 | 0.00135 | 0.32 .. 0.68 | 0.043949 | 0.042599 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.94367 | -9.0309e-05 | <= 4.5 | 3.5562 | 3.5563 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2053 | -3.51e-06 | >= 2.13 | 0.075295 | 0.075291 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2373 | -3.1e-07 | <= 1.25 | 0.01271 | 0.01271 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.751 | -2.6071e-05 | 58.8 .. 61 | 0.95109 | 0.95107 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051837 | 1.3618e-05 | <= 0.5 | 0.44818 | 0.44816 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1634 | 0.00013777 | >= 2.13 | 0.033241 | 0.033379 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.1784 | 0.00014065 | <= 1.19 | 0.011732 | 0.011591 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.822 | -1.9493e-05 | 58.8 .. 61 | 1.0218 | 1.0217 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039786 | 2.0245e-05 | <= 0.5 | 0.46023 | 0.46021 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1655 | 0.00015714 | >= 2.13 | 0.035369 | 0.035526 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1804 | 0.00016036 | <= 1.19 | 0.009744 | 0.0095837 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.82 | -1.9363e-05 | 58.8 .. 61 | 1.0201 | 1.0201 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 18.213 | 0.02077 | <= 50 | 31.808 | 31.787 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 23.214 | 3.4164 | <= 50 | 30.202 | 26.786 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 30.239 | -0.02588 | <= 50 | 19.735 | 19.761 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6667 | 0.028774 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.4286 | -0.08822 | <= 6.75 | 1.2332 | 1.3214 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.5599 | 0.022076 | <= 6.75 | 1.2122 | 1.1901 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 8.5039 | -0.0019841 | <= 9.75 | 1.2442 | 1.2461 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 9.8731 | 2.3521 | <= 12 | 4.479 | 2.1269 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | 7.093e-08 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6512 | -9.4319e-08 | 1.6 .. 1.7 | 0.048847 | 0.048847 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.8829 | 0.03634 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 5.4438 | -0.020047 | <= 6.75 | 1.2861 | 1.3062 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | 5.3335 | -0.098324 | <= 6.75 | 1.3182 | 1.4165 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 7.2059 | -0.12439 | <= 9.75 | 2.4198 | 2.5441 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 10.291 | 2.0333 | <= 12 | 3.742 | 1.7086 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | 4.5577e-08 | 1.6 .. 1.7 | 0.049736 | 0.049736 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | -3.4923e-06 | 1.6 .. 1.7 | 0.049757 | 0.049761 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.072 | 0.047461 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | 5.5663 | -0.025691 | <= 6.75 | 1.1581 | 1.1837 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | 5.5751 | -0.0063892 | <= 6.75 | 1.1685 | 1.1749 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 8.4219 | -0.14874 | <= 9.75 | 1.1794 | 1.3281 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 9.6833 | 0.21794 | <= 12 | 2.5346 | 2.3167 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -3.0648e-08 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6508 | -1.5718e-05 | 1.6 .. 1.7 | 0.049201 | 0.049217 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.4271 | 0.0023772 | <= 9.75 | 2.3253 | 2.3229 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.1333 | 0.00079948 | <= 12 | 2.8675 | 2.8667 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | 1.5197e-07 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.4911 | -0.0228 | <= 9.75 | 3.2361 | 3.2589 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.6465 | -0.1924 | <= 12 | 4.1611 | 4.3535 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | 6.0096e-08 | 1.6 .. 1.7 | 0.049737 | 0.049736 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.6298 | 0.0010267 | <= 9.75 | 2.1213 | 2.1202 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.1423 | -0.00090688 | <= 12 | 2.8568 | 2.8577 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -2.0238e-09 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.789 | -2.4525e-05 | 59 .. 61 | 0.78902 | 0.789 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 975.11 | -0.0078448 | >= 300 | 675.12 | 675.11 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.6511 | 0 | 1.5 .. 1.8 | 0.14886 | 0.14886 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.095313 | -8.3534e-06 | <= 0.5 | 0.40468 | 0.40469 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | 59.816 | 2.6893e-05 | 59 .. 61 | 0.81645 | 0.81647 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 409.06 | 0.00039375 | >= 300 | 109.06 | 109.06 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 1.6893 | 0.03003 | 1.5 .. 1.8 | 0.14077 | 0.11074 | PASS |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_ac_junction | typ | g_mid_db | 59.81 | 59.81 | 8.2393e-05 | 59 .. 61 | 0.80975 | 0.80983 | PASS |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 635.83 | 0.0046828 | >= 300 | 335.83 | 335.83 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 1.6895 | 0.02508 | 1.5 .. 1.8 | 0.13559 | 0.11051 | PASS |
| amp_ac_junction | typ | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | 11.263 | -0.0015342 | |x| <= 30 | 18.735 | 18.737 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | 8.6598 | 0.054973 | |x| <= 30 | 21.395 | 21.34 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | 9.6671 | 0.058078 | |x| <= 30 | 20.391 | 20.333 | PASS |

## pex_leak_10n

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_ac | ff85 | g_mid_db | 59.82 | 59.82 | -2.2425e-05 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ff85 | f_lo_hz | 0.27565 | 0.27566 | 1.3429e-05 | <= 0.5 | 0.22435 | 0.22434 | PASS |
| amp_ac | ff85 | f_hi_hz | 972.5 | 972.5 | -0.0042849 | >= 300 | 672.5 | 672.5 | PASS |
| amp_ac | ff85 | idd_ua | 118.81 | 118.82 | 0.01 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ff85 | vout_v | 1.651 | 1.651 | -1e-05 | 1.6 .. 1.7 | 0.04903 | 0.04904 | PASS |
| amp_ac | ff85 | hf_dev_db | 1.0739 | 1.0747 | 0.00082175 | <= 2 | 0.92608 | 0.92526 | PASS |
| amp_ac | ss-40 | g_mid_db | 59.844 | 59.844 | -4.0314e-05 | |change| <= 0.3 | - | - | PASS |
| amp_ac | ss-40 | f_lo_hz | 0.28376 | 0.28324 | -0.00051935 | <= 0.5 | 0.21624 | 0.21676 | PASS |
| amp_ac | ss-40 | f_hi_hz | 408.49 | 408.49 | -0.0014021 | >= 300 | 108.49 | 108.49 | PASS |
| amp_ac | ss-40 | idd_ua | 47.133 | 47.143 | 0.01 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | ss-40 | vout_v | 1.6501 | 1.6501 | 1e-05 | 1.6 .. 1.7 | 0.04993 | 0.04992 | PASS |
| amp_ac | ss-40 | hf_dev_db | 1.3234 | 1.3236 | 0.00014178 | <= 2 | 0.67657 | 0.67642 | PASS |
| amp_ac | typ | g_mid_db | 59.84 | 59.839 | -0.00027245 | |change| <= 0.3 | - | - | PASS |
| amp_ac | typ | f_lo_hz | 0.24144 | 0.2414 | -4.945e-05 | <= 0.5 | 0.25856 | 0.2586 | PASS |
| amp_ac | typ | f_hi_hz | 634.4 | 634.43 | 0.02752 | >= 300 | 334.4 | 334.43 | PASS |
| amp_ac | typ | idd_ua | 74.43 | 74.44 | 0.01 | x / baseline 0.95 .. 1.05 | - | - | PASS |
| amp_ac | typ | vout_v | 1.6506 | 1.6506 | 4e-05 | 1.6 .. 1.7 | 0.0494 | 0.04936 | PASS |
| amp_ac | typ | hf_dev_db | 1.0776 | 1.0775 | -9.8151e-05 | <= 2 | 0.92239 | 0.92249 | PASS |
| amp_noise | ff85 | noise_d8_post_uv | 2.1531 | 2.1531 | -3.7822e-05 | <= 2.2 | 0.046855 | 0.046892 | PASS |
| amp_noise | ss-40 | noise_d8_post_uv | 1.7415 | 1.7416 | 9.8309e-05 | <= 2 | 0.25853 | 0.25843 | PASS |
| amp_noise | typ | noise_d8_post_uv | 1.9018 | 1.9018 | 5.1586e-06 | <= 2 | 0.098172 | 0.098167 | PASS |
| amp_loop | ff85 | pm_deg | 436.63 | 436.63 | -0.003 | >= 60 | 376.63 | 376.63 | PASS |
| amp_loop | ss-40 | pm_deg | 441.13 | 441.13 | -0.001 | >= 60 | 381.13 | 381.13 | PASS |
| amp_loop | typ | pm_deg | 439.31 | 439.3 | -0.002 | >= 60 | 379.31 | 379.3 | PASS |
| amp_psrr | ff85 | supply_gain_50hz | 0.66495 | 0.66619 | 0.001239 | 0.32 .. 0.68 | 0.015047 | 0.013808 | PASS |
| amp_psrr | ss-40 | supply_gain_50hz | 0.61748 | 0.6189 | 0.001422 | 0.32 .. 0.68 | 0.062521 | 0.061099 | PASS |
| amp_psrr | typ | supply_gain_50hz | 0.63605 | 0.6374 | 0.001345 | 0.32 .. 0.68 | 0.043949 | 0.042604 | PASS |
| amp_thd | ff85 | thd_pct | 0.94376 | 0.94365 | -0.00010868 | <= 4.5 | 3.5562 | 3.5563 | PASS |
| amp_thd | ff85 | out_max_v | 2.2053 | 2.2053 | -1.35e-06 | >= 2.13 | 0.075295 | 0.075293 | PASS |
| amp_thd | ff85 | out_min_v | 1.2373 | 1.2373 | 4e-07 | <= 1.25 | 0.01271 | 0.01271 | PASS |
| amp_thd | ff85 | gain_db | 59.751 | 59.751 | -2.4373e-05 | 58.8 .. 61 | 0.95109 | 0.95107 | PASS |
| amp_thd | ss-40 | thd_pct | 0.051824 | 0.051881 | 5.7315e-05 | <= 0.5 | 0.44818 | 0.44812 | PASS |
| amp_thd | ss-40 | out_max_v | 2.1632 | 2.1635 | 0.00026689 | >= 2.13 | 0.033241 | 0.033508 | PASS |
| amp_thd | ss-40 | out_min_v | 1.1783 | 1.1785 | 0.00025857 | <= 1.19 | 0.011732 | 0.011473 | PASS |
| amp_thd | ss-40 | gain_db | 59.822 | 59.822 | -1.4353e-05 | 58.8 .. 61 | 1.0218 | 1.0217 | PASS |
| amp_thd | typ | thd_pct | 0.039765 | 0.039835 | 6.9883e-05 | <= 0.5 | 0.46023 | 0.46016 | PASS |
| amp_thd | typ | out_max_v | 2.1654 | 2.1655 | 0.00013367 | >= 2.13 | 0.035369 | 0.035503 | PASS |
| amp_thd | typ | out_min_v | 1.1803 | 1.1804 | 0.00012847 | <= 1.19 | 0.009744 | 0.0096156 | PASS |
| amp_thd | typ | gain_db | 59.82 | 59.82 | -2.6092e-05 | 58.8 .. 61 | 1.0201 | 1.0201 | PASS |
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 18.092 | -0.09989 | <= 50 | 31.808 | 31.908 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 19.704 | -0.09332 | <= 50 | 30.202 | 30.296 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 30.06 | -0.20559 | <= 50 | 19.735 | 19.94 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6606 | 0.022708 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 4.4707 | -1.0461 | <= 6.75 | 1.2332 | 2.2793 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 4.6101 | -0.92774 | <= 6.75 | 1.2122 | 2.1399 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 2.9334 | -5.5725 | <= 9.75 | 1.2442 | 6.8166 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 7.3777 | -0.1433 | <= 12 | 4.479 | 4.6223 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | 8.4923e-07 | 1.6 .. 1.7 | 0.048911 | 0.04891 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.651 | -0.00017497 | 1.6 .. 1.7 | 0.048847 | 0.049021 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.8826 | 0.03605 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 3.0858 | -2.3781 | <= 6.75 | 1.2861 | 3.6642 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | 2.88 | -2.5518 | <= 6.75 | 1.3182 | 3.87 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 1.6081 | -5.7222 | <= 9.75 | 2.4198 | 8.1419 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 6.1275 | -2.1306 | <= 12 | 3.742 | 5.8725 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.4531e-06 | 1.6 .. 1.7 | 0.049736 | 0.049741 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | -4.0177e-05 | 1.6 .. 1.7 | 0.049757 | 0.049797 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0615 | 0.03691 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | 4.8268 | -0.76518 | <= 6.75 | 1.1581 | 1.9232 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | 5.001 | -0.58048 | <= 6.75 | 1.1685 | 1.749 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 5.8903 | -2.6804 | <= 9.75 | 1.1794 | 3.8597 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 7.2175 | -2.2478 | <= 12 | 2.5346 | 4.7825 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | 6.2335e-07 | 1.6 .. 1.7 | 0.049257 | 0.049256 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6506 | -0.00017858 | 1.6 .. 1.7 | 0.049201 | 0.04938 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.4342 | 0.0095541 | <= 9.75 | 2.3253 | 2.3158 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.1385 | 0.0060265 | <= 12 | 2.8675 | 2.8615 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | 7.0082e-07 | 1.6 .. 1.7 | 0.048911 | 0.04891 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.5025 | -0.0114 | <= 9.75 | 3.2361 | 3.2475 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.6506 | -0.18831 | <= 12 | 4.1611 | 4.3494 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | 4.6744e-07 | 1.6 .. 1.7 | 0.049737 | 0.049736 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.6351 | 0.0063643 | <= 9.75 | 2.1213 | 2.1149 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.1485 | 0.0052371 | <= 12 | 2.8568 | 2.8515 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | 6.6504e-07 | 1.6 .. 1.7 | 0.049257 | 0.049256 | PASS |
| amp_ac_junction | ff85 | g_mid_db | 59.789 | 59.789 | -3.6563e-05 | 59 .. 61 | 0.78902 | 0.78898 | PASS |
| amp_ac_junction | ff85 | f_hi_hz | 975.12 | 975.12 | -0.0047069 | >= 300 | 675.12 | 675.12 | PASS |
| amp_ac_junction | ff85 | vout_v | 1.6511 | 1.6511 | 1e-05 | 1.5 .. 1.8 | 0.14886 | 0.14885 | PASS |
| amp_ac_junction | ff85 | f_lo_hz | 0.095322 | 0.095239 | -8.2767e-05 | <= 0.5 | 0.40468 | 0.40476 | PASS |
| amp_ac_junction | ss-40 | g_mid_db | 59.816 | 59.816 | -0.00019661 | 59 .. 61 | 0.81645 | 0.81625 | PASS |
| amp_ac_junction | ss-40 | f_hi_hz | 409.06 | 408.99 | -0.072826 | >= 300 | 109.06 | 108.99 | PASS |
| amp_ac_junction | ss-40 | vout_v | 1.6592 | 1.9594 | 0.30022 | 1.5 .. 1.8 | 0.14077 | -0.15945 | FAIL |
| amp_ac_junction | ss-40 | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_ac_junction | typ | g_mid_db | 59.81 | 59.81 | 0.00070189 | 59 .. 61 | 0.80975 | 0.81045 | PASS |
| amp_ac_junction | typ | f_hi_hz | 635.83 | 636.16 | 0.33266 | >= 300 | 335.83 | 336.16 | PASS |
| amp_ac_junction | typ | vout_v | 1.6644 | 1.9048 | 0.2404 | 1.5 .. 1.8 | 0.13559 | -0.10481 | FAIL |
| amp_ac_junction | typ | f_lo_hz | nan | nan | nan | nan allowed | - | - | PASS |
| amp_reset_host_junction | ff85 | drift_mv_s_os10m | 11.265 | 11.233 | -0.031753 | |x| <= 30 | 18.735 | 18.767 | PASS |
| amp_reset_host_junction | ss-40 | drift_mv_s_os10m | 8.6048 | 9.2049 | 0.60004 | |x| <= 30 | 21.395 | 20.795 | PASS |
| amp_reset_host_junction | typ | drift_mv_s_os10m | 9.609 | 10.193 | 0.58432 | |x| <= 30 | 20.391 | 19.807 | PASS |

## pex_ctl_1f

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 18.178 | -0.0141 | <= 50 | 31.808 | 31.822 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 19.817 | 0.0197 | <= 50 | 30.202 | 30.183 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 30.276 | 0.01034 | <= 50 | 19.735 | 19.724 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6215 | -0.016433 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.4726 | -0.044146 | <= 6.75 | 1.2332 | 1.2774 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.5065 | -0.031374 | <= 6.75 | 1.2122 | 1.2435 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 8.437 | -0.068814 | <= 9.75 | 1.2442 | 1.313 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 9.5917 | 2.0707 | <= 12 | 4.479 | 2.4083 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -7.0143e-09 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6511 | -8.0683e-06 | 1.6 .. 1.7 | 0.048847 | 0.048855 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.899 | 0.05246 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 5.461 | -0.0028366 | <= 6.75 | 1.2861 | 1.289 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | 5.4254 | -0.0063961 | <= 6.75 | 1.3182 | 1.3246 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 7.3009 | -0.029348 | <= 9.75 | 2.4198 | 2.4491 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 7.8371 | -0.42098 | <= 12 | 3.742 | 4.1629 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | 6.8283e-09 | 1.6 .. 1.7 | 0.049736 | 0.049736 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | -8.6345e-07 | 1.6 .. 1.7 | 0.049757 | 0.049758 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0211 | -0.003451 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | 5.5912 | -0.00070218 | <= 6.75 | 1.1581 | 1.1588 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | 5.5625 | -0.018963 | <= 6.75 | 1.1685 | 1.1875 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 8.5718 | 0.0011969 | <= 9.75 | 1.1794 | 1.1782 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 9.5283 | 0.062965 | <= 12 | 2.5346 | 2.4717 | PASS |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | 1.242e-08 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6508 | 1.2753e-07 | 1.6 .. 1.7 | 0.049201 | 0.049201 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.4247 | -1e-08 | <= 9.75 | 2.3253 | 2.3253 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.1325 | -9e-08 | <= 12 | 2.8675 | 2.8675 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -4.4696e-10 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.5185 | 0.0046 | <= 9.75 | 3.2361 | 3.2315 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.7269 | -0.11201 | <= 12 | 4.1611 | 4.2731 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -4.3046e-09 | 1.6 .. 1.7 | 0.049737 | 0.049737 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.6287 | -3e-08 | <= 9.75 | 2.1213 | 2.1213 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.144 | 0.00079999 | <= 12 | 2.8568 | 2.856 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -3.9176e-09 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |

## pex_check_nodiodes

| check | corner | value | without pad | with pad | delta | limit | margin without | margin with | result |
|---|---|---|---|---|---|---|---|---|---|
| amp_pwrup | ff85 | err_1s_mv | 18.192 | 18.173 | -0.01975 | <= 50 | 31.808 | 31.827 | PASS |
| amp_pwrup | ss-40 | err_1s_mv | 19.798 | 19.894 | 0.09611 | <= 50 | 30.202 | 30.106 | PASS |
| amp_pwrup | typ | err_1s_mv | 30.265 | 30.248 | -0.01725 | <= 50 | 19.735 | 19.752 | PASS |
| amp_reset | ff85 | t_fs_ms_os10m | 1.6379 | 1.6905 | 0.052582 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ff85 | t_1mv_s_os0 | 5.5168 | 5.4709 | -0.045932 | <= 6.75 | 1.2332 | 1.2791 | PASS |
| amp_reset | ff85 | t_1mv_s_os1m | 5.5378 | 5.4967 | -0.04115 | <= 6.75 | 1.2122 | 1.2533 | PASS |
| amp_reset | ff85 | t_1mv_s_os10m | 8.5058 | 8.6731 | 0.16726 | <= 9.75 | 1.2442 | 1.0769 | PASS |
| amp_reset | ff85 | t_1mv_s_os100m | 7.521 | 9.7165 | 2.1954 | <= 12 | 4.479 | 2.2835 | PASS |
| amp_reset | ff85 | final_v_os100m | 1.6511 | 1.6511 | -7.2883e-09 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset | ff85 | final_v_os10m | 1.6512 | 1.6512 | 2.1713e-05 | 1.6 .. 1.7 | 0.048847 | 0.048825 | PASS |
| amp_reset | ss-40 | t_fs_ms_os10m | 5.8466 | 5.9846 | 0.13804 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | ss-40 | t_1mv_s_os0 | 5.4639 | 5.4587 | -0.0051639 | <= 6.75 | 1.2861 | 1.2913 | PASS |
| amp_reset | ss-40 | t_1mv_s_os1m | 5.4318 | 5.4585 | 0.026673 | <= 6.75 | 1.3182 | 1.2915 | PASS |
| amp_reset | ss-40 | t_1mv_s_os10m | 7.3302 | 7.1394 | -0.19084 | <= 9.75 | 2.4198 | 2.6106 | PASS |
| amp_reset | ss-40 | t_1mv_s_os100m | 8.258 | 8.1634 | -0.0946 | <= 12 | 3.742 | 3.8366 | PASS |
| amp_reset | ss-40 | final_v_os100m | 1.6503 | 1.6503 | 4.5641e-08 | 1.6 .. 1.7 | 0.049736 | 0.049736 | PASS |
| amp_reset | ss-40 | final_v_os10m | 1.6502 | 1.6502 | -5.2754e-06 | 1.6 .. 1.7 | 0.049757 | 0.049762 | PASS |
| amp_reset | typ | t_fs_ms_os10m | 3.0246 | 3.0291 | 0.004559 | x / baseline 0.7 .. 1.4 | - | - | PASS |
| amp_reset | typ | t_1mv_s_os0 | 5.5919 | 5.5909 | -0.0010923 | <= 6.75 | 1.1581 | 1.1591 | PASS |
| amp_reset | typ | t_1mv_s_os1m | 5.5815 | 5.6049 | 0.023385 | <= 6.75 | 1.1685 | 1.1451 | PASS |
| amp_reset | typ | t_1mv_s_os10m | 8.5706 | 8.5706 | 1.264e-05 | <= 9.75 | 1.1794 | 1.1794 | PASS |
| amp_reset | typ | t_1mv_s_os100m | 9.4654 | 12.535 | 3.0701 | <= 12 | 2.5346 | -0.53543 | FAIL |
| amp_reset | typ | final_v_os100m | 1.6507 | 1.6507 | -1.2181e-08 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
| amp_reset | typ | final_v_os10m | 1.6508 | 1.6508 | -6.4179e-09 | 1.6 .. 1.7 | 0.049201 | 0.049201 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os10m | 7.4247 | 7.4249 | 0.00016082 | <= 9.75 | 2.3253 | 2.3251 | PASS |
| amp_reset_host | ff85 | t_1mv_s_os100m | 9.1325 | 9.1324 | -3.704e-05 | <= 12 | 2.8675 | 2.8676 | PASS |
| amp_reset_host | ff85 | final_v_os100m | 1.6511 | 1.6511 | -2.4678e-09 | 1.6 .. 1.7 | 0.048911 | 0.048911 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os10m | 6.5139 | 6.4677 | -0.0462 | <= 9.75 | 3.2361 | 3.2823 | PASS |
| amp_reset_host | ss-40 | t_1mv_s_os100m | 7.8389 | 7.6454 | -0.19348 | <= 12 | 4.1611 | 4.3546 | PASS |
| amp_reset_host | ss-40 | final_v_os100m | 1.6503 | 1.6503 | -2.9747e-09 | 1.6 .. 1.7 | 0.049737 | 0.049737 | PASS |
| amp_reset_host | typ | t_1mv_s_os10m | 7.6287 | 7.6291 | 0.00033885 | <= 9.75 | 2.1213 | 2.1209 | PASS |
| amp_reset_host | typ | t_1mv_s_os100m | 9.1432 | 9.1439 | 0.00064434 | <= 12 | 2.8568 | 2.8561 | PASS |
| amp_reset_host | typ | final_v_os100m | 1.6507 | 1.6507 | -2.7087e-09 | 1.6 .. 1.7 | 0.049257 | 0.049257 | PASS |
