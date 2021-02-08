# FNF/SM converter
Roughly convert Friday Night Funkin .json charts to doubles simfiles for Stepmania \
Or convert Stepmania simfiles to FNF charts. \
Very WIP but it works, kinda.

Usage: Drag-and-drop the FNF .json chart or a Stepmania .sm simfile onto `fnf-to-sm.exe` \
Or use the command line: `python fnf-to-sm.py [chart_file]`

For FNF-to-SM, if you input the Normal difficulty .json, and have the \
easy & hard .jsons in the same folder, then FNF-to-SM will output \
a single .sm with all 3 difficulties.

SM-to-FNF currently only supports Challenge Single difficulty. \
The output "blammed.json" is meant to replace "Blammed", Normal difficulty.

Written by shockdude in Python 3.7 \
Original chart-to-sm.js by Paturages \
https://github.com/Paturages/

Stepmania 5.3 Outfox: https://projectmoon.dance/ \
Friday Night Funkin: https://ninja-muffin24.itch.io/funkin
