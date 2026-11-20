# REVIEW.md: feedback to the layout phases

Written ONLY by the user / the monitoring session. A phase never edits this file. Every phase starts with `git pull`, reads this file and applies every open item addressed to it or to
an earlier phase BEFORE its own work (a fix to a finished phase is redone and that phase's gate re-run first), then lists the items it handled in section 9 of its report
AFE/layout/reports/<phase>.md. `gate.py` fails while an open item for the phase (or an earlier one) is not listed in a report's section 9.
ACCEPT.md is IN FORCE (user, 2026-11-20) and is reviewed after the fact: changes to it, to the limits or to a protected file arrive here as items.

Item format (one per heading; the target is a phase, several phases separated by commas, or `all`):

    ### R1 (2026-11-21) to L2b: <short title>
    Status: open
    <what to do, why, evidence>

The monitoring session sets `Status: closed` once it has seen the item handled.

## Items

(none yet)


