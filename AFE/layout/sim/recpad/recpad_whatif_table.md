# R13 recpad_table.md (written by mk_tables.py; limits = AFE/layout/accept_limits.json, Decision 51)

| case | rows with a limit | with the pad | without the pad | compare.py verdict |
|---|---|---|---|---|
| pex_ctl_1f | 33 | 33 PASS / 0 WARN / 0 FAIL | 0 FAIL | FAIL |
| pex_check_nodiodes | 33 | 32 PASS / 0 WARN / 1 FAIL | 0 FAIL | FAIL |

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
