# <phase> report (<date>; <model / effort>)

Copy to AFE/layout/reports/<phase>.md. Keep the ten headings exactly ("## n. ..."): gate.py checks them. Every number carries its source log.

## 1. Summary and verdict
<three to six lines: what the phase delivered, the gate verdict, anything the next phase must know first>

## 2. What was built
<cells, W x H, area vs the slot / estimate, files (scripts, GDS, netlists)>

## 3. Commands run
<exact commands, in order, including the ones that failed>

## 4. Results
| check | value | limit | PASS / WARN / FAIL | source log |
|---|---|---|---|---|

## 5. Gate output
<the output of `python3 AFE/layout/scripts/gate.py <phase>` copied verbatim, after it passed>

## 6. Ladder decisions
<every ACCEPT.md ladder entry applied: entry id, trigger (the failing line), evidence, what it cost; "none" if none>

## 7. Deviations
<every deviation from SPEC.md / floorplan.json / the prompt, and why; "none" if none>

## 8. Open issues and risks
<for later phases>

## 9. REVIEW.md items handled
<item ids (R<n>) with what was done; "none" if no open item>

## 10. Files changed and commit
<files (git show --stat), the commit hash (written after the commit, then pushed with a second small commit)>
