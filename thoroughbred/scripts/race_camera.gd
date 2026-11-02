extends Camera3D
## Follows the race. Five shots, switched with keys 1–5 (or C to cycle):
##   1 TV camera (side-on, from the stands side, like racing on television)
##   2 Behind the field
##   3 Head-on
##   4 Follow your horse (the one with the gold triangle)
##   5 Finish-line camera

const MODES := ["TV camera", "Behind the field", "Head-on", "Follow your horse", "Finish-line camera"]

var mode := 0
var race: Node3D
var _focus := Vector3.ZERO
var _snap := true


func setup(r: Node3D) -> void:
	race = r


func set_mode(m: int) -> void:
	mode = posmod(m, MODES.size())
	_snap = true
	race.hud.flash(MODES[mode], 1.2)


func _process(delta: float) -> void:
	if race == null or race.runners.is_empty():
		return

	# Where is the field?
	var lead_x := -INF
	var last_x := INF
	var mid_z: float = race.track_width / 2.0
	for r in race.runners:
		lead_x = maxf(lead_x, r.position.x)
		last_x = minf(last_x, r.position.x)
	var pack_x := lerpf(last_x, lead_x, 0.6)
	var mine: Node3D = race.my_runner()

	var want_pos: Vector3
	var want_focus: Vector3
	var want_fov := 40.0
	match mode:
		0:  # TV side-on: long lens from beyond the near rail, slightly behind the pack
			want_focus = Vector3(pack_x + 3.0, 1.3, mid_z)
			want_pos = Vector3(pack_x - 6.0, 6.5, mid_z + 38.0)
			want_fov = 24.0
		1:  # behind the field, raised
			want_focus = Vector3(lead_x + 4.0, 1.0, mid_z)
			want_pos = Vector3(last_x - 13.0, 6.0, mid_z + 2.0)
			want_fov = 50.0
		2:  # head-on, out in front of the leader
			want_focus = Vector3(pack_x, 1.6, mid_z)
			want_pos = Vector3(lead_x + 28.0, 2.6, mid_z - 2.0)
			want_fov = 30.0
		3:  # tight on your horse
			want_focus = mine.position + Vector3(1.8, 1.7, 0.0)
			want_pos = mine.position + Vector3(-6.5, 2.8, 7.0)
			want_fov = 55.0
		4:  # fixed camera on the finish line, panning with the leaders
			want_focus = Vector3(lead_x, 1.4, mid_z)
			want_pos = Vector3(race.race_distance + 1.0, 7.0, race.track_width + 30.0)
			want_fov = 30.0 if lead_x > race.race_distance - 250.0 else 18.0

	if _snap:
		position = want_pos
		_focus = want_focus
		fov = want_fov
		_snap = false
	else:
		# Follow along the track exactly; smooth only the other movements.
		var k := 1.0 - exp(-delta * 3.0)
		position = Vector3(want_pos.x, lerpf(position.y, want_pos.y, k), lerpf(position.z, want_pos.z, k))
		if mode == 4:
			position = want_pos
		_focus = Vector3(want_focus.x, lerpf(_focus.y, want_focus.y, k), lerpf(_focus.z, want_focus.z, k))
		fov = lerpf(fov, want_fov, k)
	look_at(_focus)
