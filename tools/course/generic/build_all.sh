#!/bin/sh
# Build the generic courses end to end (the course files, the plan, the stands, the race view, the par times).
#   sh tools/course/generic/build_all.sh [ids...]        (no ids: all twenty)
# The pars are calibrated on the bigger-stands course and copied to the smaller (the same track). CAL="races rounds".
set -e
cd "$(dirname "$0")/../../.."
ALL=""
for f in park tight ring hill downs; do for h in l r; do for s in big small; do ALL="$ALL gen-$f-$h-$s"; done; done; done
IDS=${*:-$ALL}
python3 tools/course/generic/generic_courses.py $IDS
for c in $IDS; do
  python3 tools/course/real/layout.py $c > /tmp/gen-layout-$c.txt
  python3 tools/course/real/merge_stands.py $c > /tmp/gen-stands-$c.txt
  python3 tools/course/real/to_race_view.py $c > /tmp/gen-rv-$c.txt
  case $c in
    *-big) node tools/course/real/calibrate.mjs $c ${CAL:-150 2} > /tmp/gen-cal-$c.txt ;;
    *-small) b=${c%-small}-big; [ -f tools/course/real/$b-par.json ] && cp tools/course/real/$b-par.json tools/course/real/$c-par.json ;;
  esac
  python3 tools/course/real/to_race_view.py $c > /tmp/gen-rv-$c.txt
  echo "$c done: $(grep -o '"trees": [0-9]*' /tmp/gen-rv-$c.txt) $(grep -o '"stand people": [0-9]*' /tmp/gen-rv-$c.txt)"
done
