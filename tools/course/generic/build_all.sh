#!/bin/sh
# Build the generic courses end to end (the course files, the plan, the stands, the race view, the par times).
#   sh tools/course/generic/build_all.sh [ids...]        (no ids: all ten)
# Calibration: CAL="races rounds" (default "150 2").
set -e
cd "$(dirname "$0")/../../.."
IDS=${*:-"gen-park-l gen-park-r gen-tight-l gen-tight-r gen-ring-l gen-ring-r gen-hill-l gen-hill-r gen-downs-l gen-downs-r"}
python3 tools/course/generic/generic_courses.py $IDS
for c in $IDS; do
  python3 tools/course/real/layout.py $c > /tmp/gen-layout-$c.txt
  python3 tools/course/real/merge_stands.py $c > /tmp/gen-stands-$c.txt
  python3 tools/course/real/to_race_view.py $c > /tmp/gen-rv-$c.txt
  node tools/course/real/calibrate.mjs $c ${CAL:-150 2} > /tmp/gen-cal-$c.txt
  python3 tools/course/real/to_race_view.py $c > /tmp/gen-rv-$c.txt
  echo "$c done: $(grep -o '"trees": [0-9]*' /tmp/gen-rv-$c.txt) $(grep -o '"stand people": [0-9]*' /tmp/gen-rv-$c.txt)"
done
