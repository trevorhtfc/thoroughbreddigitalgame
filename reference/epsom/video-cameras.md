# Epsom: the cameras in the owner's Racing TV Derby (18 Nov 2026)

The owner's screen recording of a 1m4f race (2m35s; the picture on its side), looked at a frame every 3 seconds. The
seconds are into the video; "metres to go" is rough (the field ran the 2,423 m in about 155 s). What each camera is and
which of the race view's cameras stands in for it (`race-view/assets/course/epsom-view.json`, written by
`tools/course/epsom/to_race_view.py`; the director's `raceDirector.shots`).

| Video | Metres to go | The camera | Race view |
|---|---|---|---|
| 0–6 s | at the start | low, inside the inside rail in front of the stalls, looking back across their faces; the woods behind them | `start` (now `inside`, 3 m in) |
| 9–27 s | 2,300–2,000 | low cameras just inside the inside rail, long lenses, the field coming at them up the hill and passing; the far rail's boards, the woods behind | `rail_1`, `rail_2` |
| 30–51 s | 1,950–1,650 | the same along the climb: the far rail's boards, the course's 4x4s outside it, woods | `rail_3` |
| 54 s | ~1,600 | low inside at the top of the hill, across the track: the long view over the countryside behind | `top` |
| 57–63 s | ~1,550–1,450 | raised head-on, on the outside of the bend, looking back up it: the field coming down at it | `headon_1` |
| 66 s | ~1,400 | high, abreast, looking down across the field at the inside rail and the road behind it | `side_1` |
| 69–75 s | ~1,350–1,250 | low inside the rail, the field passing | (the side and head-on cameras cover it) |
| 78–81 s | ~1,200–1,150 | raised head-on on the outside of the bend | `headon_2` |
| 84–87 s | ~1,100–1,050 | high side-on: the field on the inside rail, the road with people, the Downs behind with portaloos | `side_2` |
| 90 s | ~1,000 | low on the inside behind the crowd at the rail | (not used) |
| 93–99 s | ~950–850 | high head-on at Tattenham Corner, looking back up the bend | `headon_3` |
| 102–111 s | ~800–700 | high, angled down at the inside rail and the dense crowd behind it | `side_3` |
| 114–150 s | ~650–100 | high on the stand side up the course, looking back up the straight at the field: the far rail and the Hill's packed crowd behind | `straight_high` (on the Rowley stand's roof) |
| 153–162 s | the finish | from the stand, across at the Hill: the hospitality frontage with its tented roofs | `grandstand` |

Not used any more in the Derby: the tracking car (its pictures across the open Downs showed what lies beyond the course)
and the drone. The straight five furlongs keep the tracking car down the straight, then `straight_high`, then `grandstand`.
