extends Node3D
## One runner: the 3D horse and jockey, repainted in its own silks and coat,
## plus the simple speed model that moves it down the track.

const HORSE_SCENE := preload("res://assets/horses/racehorse_gallop.glb")
const RECOLOUR := preload("res://shaders/horse_recolour.gdshader")
const MASK := preload("res://assets/horses/silk_mask.png")

## One gallop loop (0.48 s) covers about 7 m of ground at the model's scale,
## so at 14.6 m/s the legs match the ground with the animation at normal speed.
const STRIDE_SPEED := 14.6
## Walking pace that matches the walk animation at normal speed.
const WALK_SPEED := 1.6
## Nose is about 1.45 m in front of the model's centre (at scale 3).
const NOSE := 1.45

var info: Dictionary            # name, silks, coat… from horse_data.gd
var lane_z := 0.0               # which lane across the track (metres)
var distance := 0.0             # metres travelled from the start
var speed := 0.0                # metres per second
var finished := false
var finish_time := 0.0
var finish_speed := 0.0

# Personality for this race (set up in setup()).
var cruise_speed := 16.6
var kick := 0.0                 # extra (or lost) speed in the closing stages
var kick_from := 250.0          # metres from home where the kick starts
var noise := FastNoiseLite.new()

var _anim: AnimationPlayer
var _marker: Node3D
var _t := 0.0


func setup(data: Dictionary, lane: float, horse_scale: float, rng: RandomNumberGenerator) -> void:
	info = data
	lane_z = lane
	name = String(data["name"]).replace(" ", "")

	var horse: Node3D = HORSE_SCENE.instantiate()
	horse.scale = Vector3.ONE * horse_scale * rng.randf_range(0.97, 1.03)
	add_child(horse)
	_paint(horse)

	_anim = horse.find_child("AnimationPlayer", true, false)
	for anim_name in ["gallop", "walk"]:
		_anim.get_animation(anim_name).loop_mode = Animation.LOOP_LINEAR
	# Stand still behind the line until the race starts.
	_anim.play("walk")
	_anim.seek(rng.randf_range(0.0, 2.0), true)
	_anim.pause()

	cruise_speed = rng.randf_range(16.5, 17.0)
	kick = rng.randf_range(-0.5, 0.9)
	kick_from = rng.randf_range(150.0, 350.0)
	noise.seed = rng.randi()
	noise.frequency = 0.15

	if data["mine"]:
		_add_marker()


## Swap the model's material for the recolour shader, with this runner's colours.
func _paint(horse: Node3D) -> void:
	for mesh_instance: MeshInstance3D in horse.find_children("*", "MeshInstance3D", true, false):
		var original := mesh_instance.mesh.surface_get_material(0) as BaseMaterial3D
		var mat := ShaderMaterial.new()
		mat.shader = RECOLOUR
		mat.set_shader_parameter("albedo_tex", original.albedo_texture)
		mat.set_shader_parameter("normal_tex", original.normal_texture)
		mat.set_shader_parameter("mask_tex", MASK)
		mat.set_shader_parameter("silk_a", info["silk_a"])
		mat.set_shader_parameter("silk_b", info["silk_b"])
		mat.set_shader_parameter("coat", info["coat"])
		mat.set_shader_parameter("points", info["points"])
		mesh_instance.material_override = mat


## The small gold triangle that floats over the player's horse.
func _add_marker() -> void:
	var tri := MeshInstance3D.new()
	var prism := PrismMesh.new()
	prism.size = Vector3(0.55, 0.5, 0.12)
	tri.mesh = prism
	tri.rotation_degrees = Vector3(180, 0, 0)  # point down
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("#e8c770")
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	tri.material_override = mat
	_marker = Node3D.new()
	_marker.position = Vector3(0.3, 2.75, 0)
	_marker.add_child(tri)
	add_child(_marker)


func start() -> void:
	_anim.play("gallop", 0.35)
	_anim.seek(randf() * 0.48, true)


## Called every physics step by the race while it is running.
func advance(delta: float, race_distance: float) -> void:
	_t += delta
	var to_go := race_distance - distance
	var target := cruise_speed
	var accel := 7.0 if distance < 40.0 else 2.5    # quick away from the stalls
	if finished:
		# pull up after the line: ease to a canter, then walk once well past the post
		target = 7.0 if -to_go < 160.0 else 1.6
		accel = 1.6
	elif to_go < kick_from:
		target += kick                              # finishing effort (or tiring)
	if not finished:
		target *= 1.0 + 0.025 * noise.get_noise_1d(_t * 10.0)

	speed = move_toward(speed, target, accel * delta)
	distance += speed * delta

	position.x = distance - NOSE   # distance is measured at the horse's nose
	position.z = lane_z + 0.35 * noise.get_noise_1d(_t * 2.0 + 500.0)   # a little drift in the lane

	if not finished or speed > 4.5:
		_anim.speed_scale = clampf(speed / STRIDE_SPEED, 0.55, 1.4)
	else:
		if _anim.current_animation != "walk":
			_anim.play("walk", 0.6)
		_anim.speed_scale = clampf(speed / WALK_SPEED, 0.6, 1.2)

	if not finished and distance >= race_distance:
		finished = true
		# time when the nose crossed the line, interpolated within this step
		finish_time = _t - (distance - race_distance) / maxf(speed, 0.1)
		finish_speed = speed


func _process(_delta: float) -> void:
	if _marker:
		_marker.position.y = 2.75 + 0.08 * sin(Time.get_ticks_msec() / 250.0)
