# RUNBOOK: running the layout phases alone (Atharv)

> **NOW (2026-11-20, Decision 48):** run the rework round R2 -> R3 / R4 / R5 in AFE/prompts/layout_run.md section "Rework round R2-R5" before L2b, L1b, L3a. Deadline 2026-11-30 (Decision 49).


Plain-language guide to AFE/prompts/layout_run.md. Nobody has to answer you: AFE/layout/ACCEPT.md is IN FORCE (user, 2026-11-20) and tells the agent what to do when something fails.
The user / monitoring session reads your reports afterwards and, if something must change, writes it into AFE/layout/REVIEW.md; the next phase you start picks it up by itself.

## Once, before the first phase
1. Start the course container (`hpretl/iic-osic-tools:chipathon26`), open a terminal in /foss/designs/ENGN2912E_Project, `git pull`.
2. `bash AFE/layout/scripts/check_env.sh` (1-2 minutes). It must end with `RESULT: OK`. Each FAIL line says what to do (`-> DO:`). Compare with AFE/layout/sim/check_env_ref.log (the LP machine).
   If the repository disk is small (A7 line): `export AFE_SCRATCH=/tmp/afe_scratch` in every terminal before you start a phase.
3. Make sure `git push` works from this machine (you push after every phase).

## Every phase, the same five steps
1. `git pull`.
2. Start a fresh Claude Code session in the repo root (`claude`), choose the model / effort of the table below.
3. Paste the phase's code block from AFE/prompts/layout_run.md (everything between the ``` lines).
4. Wait. The agent works through the phase, applies open REVIEW.md items first, and fixes failures with the ACCEPT.md ladder. Long phases push a checkpoint commit every ~2 h.
5. Done = the agent printed `GATE <phase>: PASS`, wrote AFE/layout/reports/<phase>.md, committed and pushed. Check with `git log -1` and `git status` (nothing of the phase left uncommitted), then start the next phase.

| # | phase | what | model / effort | about | may run together with | needs |
|---|---|---|---|---|---|---|
| 1 | L2a | amplifier cell (running now; its own prompt) | Sonnet 5.5 / high | - | - | - |
| 2 | L1a | ADC cell adc_ch, DRC + LVS | Sonnet 5.5 / high | 3-6 h | L1d | - |
| 3 | L1d | digital macro afe_dig (LP's recipe, ~2 min per hardening run) | Sonnet 5.5 / high | 1-2 h | L1a | - |
| 4 | L2b | amplifier PEX + post-layout simulations | Sonnet 5.5 / default | 2-4 h (simulations ~1 h) | L1b | L2a |
| 5 | L1b | ADC PEX + post-layout simulations | Sonnet 5.5 / default | 2-4 h | L2b | L1a, L1d |
| 6 | L3a | top assembly, full-chip DRC + LVS | Sonnet 5.5 / high | 6-10 h | - | L1d, L2b, L1b |
| 7 | L3b | system checks (supply, crosstalk, 8-channel power-up, end to end) | Sonnet 5.5 / default | 3-5 h | - | L3a |
| 8 | L4 | submission package | Sonnet 5.5 / default | 1-2 h | - | L3b |

Two phases at once = two terminals and two Claude sessions in the same repo; the kit limits heavy jobs to 3 at a time across both (8 GB RAM). Each session commits only its own files.

## What blocks what (if one phase is stuck, what can still run)
| stuck | can still run |
|---|---|
| L2a (amplifier) | L1a, L1d, L1b |
| L1a (ADC cell) | L1d, L2b |
| L1d (macro) | L1a, L2b; L1b with the LP trial timing (AFE/dig/reports/sta_taps.json) |
| L2b or L1b | the other one; L3a only after both (it needs the final cells) |
| L3a, L3b | nothing new: fix it (the ladder) or wait for the REVIEW.md answer |

## When a gate fails
The agent handles it: it finds the failing line in ACCEPT.md section 4 (the decision ladder: G general, D DRC, L LVS, P PEX, R amplifier, Q ADC, C digital, A area, S supply, X crosstalk,
N native-Vt device, O organizer defaults) and does what the entry says, at most a few tries. Only if no entry fits, it writes AFE/layout/BLOCKED.md (what failed, what it tried, the one
question that unblocks it), commits, pushes and stops. Then: start a phase from the "can still run" column; the answer comes through REVIEW.md, and the next phase applies it.
If the agent stops for another reason (crash, out of credits, computer restarted): start a new session with the same prompt and add the line
`RESUME: a previous session of this phase stopped half-way` (common rule 11). It continues from the first FAIL of `python3 AFE/layout/scripts/gate.py <phase> --no-findings`.

## Things you might type yourself
- `python3 AFE/layout/scripts/gate.py <phase>`: is the phase finished? (prints PASS / FAIL per line and what to do)
- `python3 AFE/layout/tb/compare.py --phase L2b` (or L1b, L3a, L3b): post-layout numbers against the limits -> AFE/layout/sim/post/compare_<phase>.md
- `python3 AFE/layout/scripts/floorplan.py check`: does everything fit the 1000 x 1000 um outline?
- `python3 AFE/layout/scripts/check_submission.py --pre`: the submission files as far as they exist.
- `python3 AFE/layout/scripts/check_prompts.py`: every file the prompts mention exists (or is made by a named phase).

## Where things are
| what | where |
|---|---|
| prompts | AFE/prompts/layout_run.md |
| floorplan, pins, cell contracts | AFE/layout/SPEC.md, AFE/layout/floorplan.json |
| limits + what to do on failure | AFE/layout/ACCEPT.md (machine copy AFE/layout/accept_limits.json) |
| feedback from the user | AFE/layout/REVIEW.md (never edit it) |
| phase reports | AFE/layout/reports/<phase>.md (template TEMPLATE.md) |
| DRC / LVS / PEX reports | AFE/layout/sim/flow/<cell>.drc.json / .lvs.json / .pex.json (by AFE/layout/scripts/flow.py) |
| pre-layout baselines / post-layout results | AFE/layout/baseline/, AFE/layout/sim/post/ |
| digital macro | AFE/dig/ (recipe AFE/dig/run_dig.sh; final files AFE/dig/final/ after L1d) |
| LVS references | AFE/layout/lvs/ (only AFE/layout/scripts/mk_lvs_netlists.py writes them) |
| design record | AFE/NOTES.md (Decisions, phase findings, Results log) |

## L4 and after
L4 prepares gds/, spice/, verilog/gl/, info.yaml, lvs_config.json, README.md and the export-control answers (documents/export_control_answers.md). A person still has to: sign the
export-control form, create / push the submission repository the organizer asks for, and send any organizer answer that is still open. The organizer builds the pad frame
(their padring fork, `SLOT=workshop make librelane`); we do not run it.
