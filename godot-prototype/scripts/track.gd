extends Node3D
## Builds a straight turf course: grass, white running rails, furlong poles,
## start and finish lines, a winning post and a tree line for a sense of speed.
## Everything is made in code from simple shapes, so there are no extra assets.

const TURF := preload("res://shaders/turf.gdshader")
const FURLONG := 201.168

var _white := _mat(Color("#f4f2ec"))


## race_distance: metres from start to finish. width: metres between the rails.
## lanes / first_lane / lane_width place the starting stalls.
func build(race_distance: float, width: float, lanes: int, first_lane: float, lane_width: float) -> void:
	var run_in := 60.0     # turf before the start
	var run_out := 250.0   # turf after the finish, for pulling up
	var length := race_distance + run_in + run_out
	var mid_x := (race_distance + run_out - run_in) / 2.0

	# Surrounding ground
	_box(Vector3(length + 600, 0.1, 500), Vector3(mid_x, -0.06, width / 2), _mat(Color("#3f5a2a"), 1.0))

	# Track turf with mown stripes
	var turf := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(length, width + 6)
	turf.mesh = plane
	var turf_mat := ShaderMaterial.new()
	turf_mat.shader = TURF
	turf.material_override = turf_mat
	turf.position = Vector3(mid_x, 0.0, width / 2)
	add_child(turf)

	# Running rails on both sides, with posts every 4 m
	for z in [0.0, width]:
		_box(Vector3(length, 0.1, 0.1), Vector3(mid_x, 1.05, z), _white)
		_posts(mid_x - length / 2, length, z)

	# Start and finish lines
	_box(Vector3(0.25, 0.02, width), Vector3(0, 0.01, width / 2), _white)
	_box(Vector3(0.25, 0.02, width), Vector3(race_distance, 0.01, width / 2), _white)

	# Furlong poles (on the far rail, counting down to the finish)
	var f := 1
	while f * FURLONG < race_distance - 20:
		var x := race_distance - f * FURLONG
		_box(Vector3(0.15, 2.2, 0.15), Vector3(x, 1.1, -0.4), _white)
		_box(Vector3(0.6, 0.6, 0.16), Vector3(x, 2.4, -0.4), _mat(Color("#c8372d")))
		var lab := Label3D.new()
		lab.text = "%df" % f
		lab.font_size = 96
		lab.pixel_size = 0.01
		lab.outline_size = 18
		lab.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lab.position = Vector3(x, 3.1, -0.4)
		add_child(lab)
		f += 1

	# Winning post on the near side: tall white pole with a red disc
	_box(Vector3(0.18, 4.0, 0.18), Vector3(race_distance, 2.0, width + 0.6), _white)
	var disc := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.55
	cyl.bottom_radius = 0.55
	cyl.height = 0.08
	disc.mesh = cyl
	disc.material_override = _mat(Color("#c8372d"))
	disc.rotation_degrees = Vector3(90, 0, 0)
	disc.position = Vector3(race_distance, 4.2, width + 0.6)
	add_child(disc)

	# Starting stalls: open green frames behind the line (posts and top beams, so the cameras can see through)
	var stall_green := _mat(Color("#2f5d3a"))
	var stalls_mid := first_lane - lane_width / 2.0 + lanes * lane_width / 2.0
	for i in lanes + 1:
		var z := first_lane - lane_width / 2.0 + i * lane_width
		for x in [-3.4, -0.4]:
			_box(Vector3(0.12, 2.7, 0.12), Vector3(x, 1.35, z), stall_green)
		_box(Vector3(3.1, 0.12, 0.1), Vector3(-1.9, 1.1, z), stall_green)   # side rail of each bay
	for x in [-3.4, -0.4]:
		_box(Vector3(0.2, 0.3, lanes * lane_width + 0.2), Vector3(x, 2.75, stalls_mid), stall_green)

	# Tree line on the far side and hedges, for depth and a sense of speed
	_trees(mid_x - length / 2 - 200, length + 400, width)
	_box(Vector3(length + 400, 1.6, 1.2), Vector3(mid_x, 0.8, -14), _mat(Color("#2f4a24")))
	_box(Vector3(length + 400, 1.6, 1.2), Vector3(mid_x, 0.8, width + 70), _mat(Color("#2f4a24")))


func _posts(x_start: float, length: float, z: float) -> void:
	var count := int(length / 4.0)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var post := BoxMesh.new()
	post.size = Vector3(0.08, 1.05, 0.08)
	mm.mesh = post
	mm.instance_count = count
	for i in count:
		mm.set_instance_transform(i, Transform3D(Basis(), Vector3(x_start + i * 4.0, 0.52, z)))
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = _white
	add_child(mmi)


func _trees(x_start: float, length: float, width: float) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var count := int(length / 9.0)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var crown := SphereMesh.new()
	crown.radius = 1.0
	crown.height = 2.0
	crown.radial_segments = 10
	crown.rings = 6
	mm.mesh = crown
	mm.instance_count = count
	for i in count:
		var s := rng.randf_range(2.8, 5.0)
		var basis := Basis().scaled(Vector3(s, s * rng.randf_range(1.0, 1.4), s))
		var pos := Vector3(x_start + i * 9.0 + rng.randf_range(-3, 3), s * 1.1, -55 - rng.randf_range(0, 30))
		mm.set_instance_transform(i, Transform3D(basis, pos))
		mm.set_instance_color(i, Color("#2e4a22").lerp(Color("#466b2c"), rng.randf()))
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 1.0
	mmi.material_override = mat
	add_child(mmi)


func _box(size: Vector3, pos: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = size
	mi.mesh = box
	mi.material_override = mat
	mi.position = pos
	add_child(mi)
	return mi


static func _mat(c: Color, rough := 0.8) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	return m
