extends CanvasLayer
## On-screen panel: race title, distance to go, running order with silks swatches,
## big messages ("They're off!") and the key help line. Built in code, in the
## Thoroughbred house colours.

const INK := Color("#33332b")
const MUTED := Color("#6b6a60")
const GREEN := Color("#3d7153")
const BAND := Color("#446f66")
const GOLD := Color("#b79042")
const PANEL := Color("#fbf9f4")
const LINE := Color("#d8d2c4")
const LENGTH := 2.4   # metres in a horse's length

var race: Node3D
var _info: Label
var _rows: VBoxContainer
var _message: Label
var _message_time := 0.0
var _row_nodes := []


func setup(r: Node3D) -> void:
	race = r

	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _box(Color(PANEL, 0.93), LINE))
	panel.position = Vector2(16, 16)
	panel.custom_minimum_size = Vector2(300, 0)
	add_child(panel)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	panel.add_child(col)

	var title := _label("TEST RACE  ·  %s STRAIGHT" % _furlongs(race.race_distance), 15, Color.WHITE)
	var band := PanelContainer.new()
	band.add_theme_stylebox_override("panel", _box(BAND, BAND, 8))
	band.add_child(title)
	col.add_child(band)
	_info = _label("", 14, MUTED)
	col.add_child(_info)
	_rows = VBoxContainer.new()
	_rows.add_theme_constant_override("separation", 2)
	col.add_child(_rows)
	for i in race.runners.size():
		_row_nodes.append(_make_row())

	_message = _label("", 40, Color.WHITE)
	_message.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7))
	_message.add_theme_constant_override("outline_size", 10)
	_message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_message.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	_message.position.y = 60
	_message.grow_horizontal = Control.GROW_DIRECTION_BOTH
	add_child(_message)

	var help := _label("1 TV  ·  2 Behind  ·  3 Head-on  ·  4 Your horse  ·  5 Finish  ·  C next camera  ·  F fast  ·  Space pause  ·  R new race", 13, Color.WHITE)
	help.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.6))
	help.add_theme_constant_override("outline_size", 5)
	help.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	help.position = Vector2(16, help.position.y - 14)
	add_child(help)


func flash(text: String, seconds := 1.5) -> void:
	_message.text = text
	_message_time = seconds
	_message.modulate.a = 1.0


func show_result() -> void:
	flash("Result", 9999.0)


func _process(delta: float) -> void:
	if race == null:
		return
	# Message fades out (real time, so it still works when paused or fast)
	var real_delta := delta / Engine.time_scale if Engine.time_scale > 0.0 else 0.016
	_message_time -= real_delta
	_message.modulate.a = clampf(_message_time / 0.4, 0.0, 1.0)

	var order: Array = race.standings()
	var leader = order[0]
	var to_go := maxf(race.race_distance - leader.distance, 0.0)
	if race.state == race.State.WAITING:
		_info.text = "At the start  ·  %d runners" % race.runners.size()
	elif race.state == race.State.RUNNING and to_go > 0.0:
		_info.text = "%d m to go  ·  %.1f s  ·  %.0f km/h" % [to_go, race.race_time, leader.speed * 3.6]
	else:
		_info.text = "Result  ·  won in %.2f s" % race.finish_order[0].finish_time

	for i in order.size():
		var r = order[i]
		var row: Dictionary = _row_nodes[i]
		row.pos.text = str(i + 1)
		row.name.text = r.info["name"]
		row.name.add_theme_color_override("font_color", GREEN if r.info["mine"] else INK)
		row.silk_a.color = r.info["silk_a"]
		row.silk_b.color = r.info["silk_b"]
		row.silk_b2.color = r.info["silk_b"]
		row.mine.visible = r.info["mine"]
		if i == 0:
			row.gap.text = ("%.2fs" % r.finish_time) if r.finished else ""
		elif r.finished and leader.finished:
			# margin at the line, in lengths, from the time gap and the winner's speed
			row.gap.text = _lengths((r.finish_time - leader.finish_time) * leader.finish_speed)
		else:
			row.gap.text = _lengths(leader.distance - r.distance)


func _make_row() -> Dictionary:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	_rows.add_child(h)
	var pos := _label("", 14, MUTED)
	pos.custom_minimum_size.x = 18
	pos.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	h.add_child(pos)
	# silks swatch: colour A body with colour B sleeves
	var swatch := HBoxContainer.new()
	swatch.add_theme_constant_override("separation", 0)
	var b1 := ColorRect.new()
	b1.custom_minimum_size = Vector2(4, 16)
	var a := ColorRect.new()
	a.custom_minimum_size = Vector2(10, 16)
	var b2 := ColorRect.new()
	b2.custom_minimum_size = Vector2(4, 16)
	for c in [b1, a, b2]:
		swatch.add_child(c)
	swatch.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(swatch)
	var name_label := _label("", 14, INK)
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(name_label)
	# the player's horse: a small gold triangle
	var mine := Control.new()
	mine.custom_minimum_size = Vector2(10, 16)
	mine.draw.connect(func(): mine.draw_colored_polygon(PackedVector2Array([Vector2(0, 4), Vector2(10, 4), Vector2(5, 12)]), GOLD))
	h.add_child(mine)
	var gap := _label("", 13, MUTED)
	gap.custom_minimum_size.x = 64
	gap.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	h.add_child(gap)
	return {"pos": pos, "name": name_label, "silk_a": a, "silk_b": b1, "silk_b2": b2, "mine": mine, "gap": gap}


func _lengths(metres: float) -> String:
	var l := metres / LENGTH
	if l < 0.05:
		return "nose"
	if l < 0.15:
		return "short head"
	if l < 0.3:
		return "head"
	if l < 0.45:
		return "neck"
	return "%.1f L" % l


static func _furlongs(m: float) -> String:
	return "%dF" % roundi(m / 201.168)


func _label(text: String, size: int, colour: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", colour)
	return l


static func _box(bg: Color, border: Color, pad := 10) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(1)
	s.set_corner_radius_all(3)
	s.content_margin_left = pad
	s.content_margin_right = pad
	s.content_margin_top = pad * 0.6
	s.content_margin_bottom = pad * 0.6
	return s
