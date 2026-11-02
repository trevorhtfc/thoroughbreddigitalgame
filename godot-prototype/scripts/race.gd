extends Node3D
## TEST RACE — step one of the 3D race view.
## Builds a straight course, loads a field of our horses in their silks and coats,
## runs a simple race and hands the action to the race camera and the on-screen panel.
##
## Keys: 1–5 cameras · C next camera · F fast-forward · Space pause · R new race

## Race length in metres (5 furlongs = 1006 m).
@export var race_distance := 1006.0
## How many runners (6–8 suits this test; up to 12 fits the track).
@export_range(2, 12) var field_size := 8
## Metres between lanes.
@export var lane_width := 1.7
## Size of the horse model in the world (3 ≈ a real thoroughbred).
@export var horse_scale := 3.0
## Seconds behind the stalls before they jump.
@export var countdown := 2.5
## 0 = a new random field each time; any other number repeats the same field.
@export var field_seed := 0

const HorseData := preload("res://scripts/horse_data.gd")
const Runner := preload("res://scripts/runner.gd")
const FIRST_LANE := 1.25   # metres from the far rail to the first lane

enum State { WAITING, RUNNING, FINISHED }

var state := State.WAITING
var runners: Array = []
var finish_order: Array = []
var race_time := 0.0
var track_width := 0.0

@onready var track := $Track
@onready var camera := $RaceCamera
@onready var hud := $HUD


func _ready() -> void:
	Engine.time_scale = 1.0
	var rng := RandomNumberGenerator.new()
	if field_seed != 0:
		rng.seed = field_seed
	else:
		rng.randomize()

	track_width = FIRST_LANE * 2.0 + (field_size - 1) * lane_width
	track.build(race_distance, track_width, field_size, FIRST_LANE, lane_width)

	# Load the field into random stalls
	var field := HorseData.make_field(field_size, rng)
	var stalls := range(field_size)
	HorseData._shuffle(stalls, rng)
	for i in field_size:
		var r := Runner.new()
		add_child(r)
		r.setup(field[i], FIRST_LANE + stalls[i] * lane_width, horse_scale, rng)
		r.set_meta("stall", stalls[i] + 1)
		r.position = Vector3(-Runner.NOSE, 0.0, r.lane_z)
		runners.append(r)

	hud.setup(self)
	camera.setup(self)
	hud.flash("They're under orders…", countdown)
	await get_tree().create_timer(countdown).timeout
	_start()


func _start() -> void:
	state = State.RUNNING
	for r in runners:
		r.start()
	hud.flash("They're off!", 1.5)


func _physics_process(delta: float) -> void:
	if state == State.WAITING:
		return
	if state == State.RUNNING:
		race_time += delta
	var just_finished := []
	for r in runners:
		r.advance(delta, race_distance)
		if r.finished and not finish_order.has(r):
			just_finished.append(r)
	if just_finished.size() > 0:
		just_finished.sort_custom(func(a, b): return a.finish_time < b.finish_time)
		finish_order.append_array(just_finished)
		if finish_order.size() == just_finished.size():
			hud.flash("Won by %s" % finish_order[0].info["name"], 3.0)
	if state == State.RUNNING and finish_order.size() == runners.size():
		state = State.FINISHED
		hud.show_result()


## Runners in race order: finishers first (in the order they crossed), then by distance.
func standings() -> Array:
	var rest := runners.filter(func(r): return not finish_order.has(r))
	rest.sort_custom(func(a, b): return a.distance > b.distance)
	return finish_order + rest


func my_runner() -> Node3D:
	for r in runners:
		if r.info["mine"]:
			return r
	return runners[0]


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	match event.keycode:
		KEY_1, KEY_2, KEY_3, KEY_4, KEY_5:
			camera.set_mode(event.keycode - KEY_1)
		KEY_C:
			camera.set_mode(camera.mode + 1)
		KEY_F:
			Engine.time_scale = 3.0 if Engine.time_scale == 1.0 else 1.0
			hud.flash("Fast-forward ×3" if Engine.time_scale > 1.0 else "Normal speed", 1.0)
		KEY_SPACE:
			Engine.time_scale = 0.0 if Engine.time_scale > 0.0 else 1.0
			hud.flash("Paused" if Engine.time_scale == 0.0 else "", 0.0 if Engine.time_scale > 0.0 else 9999.0)
		KEY_R:
			Engine.time_scale = 1.0
			get_tree().reload_current_scene()
