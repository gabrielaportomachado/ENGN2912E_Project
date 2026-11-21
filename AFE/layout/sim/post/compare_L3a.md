# compare.py L3a: AFE/layout/sim/post against AFE/layout/baseline

| check | corner | value | baseline | post-layout | change | limit | result |
|---|---|---|---|---|---|---|---|
| tgate | ff85 | ron_max_kohm | 15.605 | 15.603 | -0.001883 | <= 133 | PASS |
| tgate | ff85 | ron_max_kohm | 15.605 | 15.603 | -0.001883 | x / baseline 0.9 .. 1.1 | PASS |
| tgate | ff85 | i_off_pa | 0.012012 | 0.010649 | -0.001363 | <= 1 | PASS |
| tgate | ss-40 | ron_max_kohm | 34.233 | 34.232 | -0.001673 | <= 133 | PASS |
| tgate | ss-40 | ron_max_kohm | 34.233 | 34.232 | -0.001673 | x / baseline 0.9 .. 1.1 | PASS |
| tgate | ss-40 | i_off_pa | 0.0080767 | 0.0084005 | +0.0003238 | <= 1 | PASS |
| tgate | typ | ron_max_kohm | 21.021 | 21.019 | -0.001791 | <= 133 | PASS |
| tgate | typ | ron_max_kohm | 21.021 | 21.019 | -0.001791 | x / baseline 0.9 .. 1.1 | PASS |
| tgate | typ | i_off_pa | 0.010297 | 0.010042 | -0.0002554 | <= 1 | PASS |

RESULT compare L3a: PASS  (9 PASS, 0 WARN, 0 FAIL, 0 missing)
