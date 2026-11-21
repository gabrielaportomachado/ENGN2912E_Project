# Technical answers for documents/Export_Control_GF_Rev8.2.docx (prepared 2026-11-20, phase LP; restated 2026-11-21 by REVIEW R16 for 4 channels, 20 pads and the 605 x 1110 um outline)

Copy these into the form. Only the TECHNICAL questions are answered here. The contact fields, the questions about the parties to the transaction (2, 3, 9), the legal
classification questions (5, 10) and the signature are for the person who signs (a human; they are not answerable from the design files). Source of every statement: AFE/NOTES.md
(Decisions 1-54), README.md, AFE/review/AUDIT.md.

| field / question | answer |
|---|---|
| Customer Name | `<signer: university / course>` |
| Device Name | dbs_afe_top (pending the organizer's macro name) |
| Project Name | Chipathon 2026, team GAJT: 4-channel neural recording front end with SAR ADC |
| Phone / Contact Person / Email | `<signer>` |
| 1 a) description and end use | Academic test chip (one block inside the shared Chipathon 2026 multi-project die): 4-channel low-frequency biopotential recording front end. Per channel a 60 dB AC-coupled amplifier (0.2 Hz to about 0.4-1 kHz) and a 12-bit SAR ADC (4 kS/s), electrode routing switches, a serial (SPI-like) digital interface. End use: university teaching and bench characterisation of neural (local field potential) recording circuits; not for implantation or for connection to a person. |
| 1 b) (i) peak saturated power output | Not applicable: no RF / microwave function (no transmitter, no power amplifier). |
| 1 b) (ii) operating frequency | Digital clock 2 MHz nominal, 3 MHz maximum; analog signal band 0.2 Hz - 1 kHz; sample rate 4 kS/s per channel. |
| 1 b) (iii) fractional bandwidth | Not applicable (no RF function). |
| 1 b) (iv) planar side length | 0.605 mm x 1.110 mm (our block, Decision 52; the shared die is the organizer's) |
| 1 c) mmWave product? | No. (i)-(iv): not applicable; no phase shifter; not specially designed for telecommunications, radar or automotive; not controlled under USML XI(c)(4), XV(e)(14) or ECCN 3A001.b.2 / 3A001.b.12 / 5E001.d (no MMIC). |
| 4 more than one chip design in the tapeout? | Our project is one design. The multi-project frame of the Chipathon contains several projects: the organizer answers for the frame. |
| 6 variants that do not change end use / export outcome? | No variants. |
| 7 ASIC for a specific function? | Yes: a fixed-function mixed-signal circuit for biopotential recording (4 amplifiers + 4 ADCs + routing switches + serial interface); not programmable beyond its configuration word (channel enables, mode, amplifier reset). |
| 8 weapons / missiles / nuclear use? | No. |
| 2, 3, 5, 9, 10 | `<signer>` (parties, countries, jurisdictions, legal classification). Technical facts for 10: the design is not designed or modified for a military, space or intelligence application. |
