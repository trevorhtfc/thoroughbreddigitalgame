extends RefCounted
## Shared horse data for the 3D race view: silks, coat colours and names.
## These lists are copied from the Thoroughbred Ascot web game so the 3D horses
## match the horses the player sees there.

## Silks: [id, colour A, colour B] — same ids as img/silks/sNN.webp in the web game.
## Colour A paints the jacket hoops, colour B the other hoops and the cap.
const SILKS := [
	["s01", "#3e9745", "#d53f3c"],
	["s02", "#604a82", "#b7e5f1"],
	["s03", "#49266c", "#ffffff"],
	["s04", "#333f51", "#333f51"],
	["s05", "#2156a6", "#f1a43f"],
	["s06", "#eea1c6", "#eea1c6"],
	["s07", "#49266c", "#ffffff"],
	["s08", "#1d1d1d", "#eff5f5"],
	["s09", "#ed2f24", "#fffefe"],
	["s10", "#ed2f24", "#eff5f5"],
	["s11", "#333f51", "#b8e5f2"],
	["s12", "#bebfc0", "#bebfc0"],
	["s13", "#2156a5", "#f1dc47"],
	["s14", "#a8a8aa", "#9e3a59"],
	["s15", "#2356a6", "#ee2f24"],
	["s16", "#333f51", "#b8e5f2"],
	["s17", "#e0d5a9", "#333f51"],
	["s18", "#2156a5", "#2156a5"],
	["s19", "#b7e4f1", "#333f51"],
	["s20", "#64c3ab", "#eea1c6"],
	["s21", "#2055a6", "#feffff"],
	["s22", "#2156a5", "#ffffff"],
	["s23", "#f1e93e", "#1d1d1d"],
	["s24", "#604a82", "#64c3ab"],
	["s25", "#a04059", "#ffffff"],
	["s26", "#eff5f5", "#1d1d1d"],
	["s27", "#b7e4f1", "#f0a43f"],
	["s28", "#1d1d1d", "#f1e93e"],
	["s29", "#64c3ab", "#ffffff"],
	["s30", "#333f51", "#f1db47"],
	["s31", "#eff5f5", "#ed2e23"],
	["s32", "#1d1d1d", "#ffffff"],
	["s33", "#f0a43f", "#1d1e1e"],
	["s34", "#333f51", "#eea1c6"],
	["s35", "#eff5f5", "#eea1c6"],
	["s36", "#eff5f5", "#2056a6"],
	["s37", "#eff5f5", "#49266c"],
	["s38", "#49266c", "#eea1c6"],
	["s39", "#9e3a59", "#c98637"],
	["s40", "#eff5f5", "#ed2e23"],
	["s41", "#ed2f24", "#eff5f5"],
	["s42", "#49266c", "#ed2f24"],
	["s43", "#f1e93e", "#49266c"],
	["s44", "#2156a5", "#ffffff"],
	["s45", "#b7e4f1", "#333f51"],
	["s46", "#eda1c6", "#64c3ab"],
	["s47", "#eff5f5", "#64c3ab"],
	["s48", "#1d1d1d", "#f1e93e"],
	["s49", "#333f51", "#f1dc47"],
	["s50", "#e9c665", "#2156a6"],
	["s51", "#2156a6", "#e9c665"],
	["s52", "#eff5f5", "#2056a6"],
	["s53", "#f1e93e", "#1d1d1d"],
	["s54", "#f1e93e", "#1d1d1d"],
]

## Coats: name, body colour (from the web game) and points colour (mane, tail, lower legs).
const COATS := [
	{"name": "Bay", "body": "#7a4a2a", "points": "#1d1714"},
	{"name": "Brown", "body": "#4a2e1c", "points": "#17110d"},
	{"name": "Chestnut", "body": "#a3552c", "points": "#6a3317"},
	{"name": "Black", "body": "#2b2523", "points": "#141110"},
	{"name": "Grey", "body": "#a8a6a0", "points": "#6d6b66"},
]

const NAME_A := ["Silver", "Royal", "Golden", "Northern", "Midnight", "Crimson", "Iron", "Highland", "Copper", "Shadow", "Velvet", "Thunder", "Gilded", "Ember", "Frost", "Morning", "Harbour", "Paper", "Quiet", "Wild", "Summer", "Distant", "Lucky", "Scarlet", "Hidden", "Brave", "Salt", "Amber", "Lantern", "Starlit"]
const NAME_B := ["Crown", "Echo", "Harbour", "Comet", "Ridge", "Sonnet", "Banner", "Sovereign", "Quarry", "Falcon", "Meadow", "Tempest", "Rampart", "Cadence", "Arrow", "Monarch", "Reverie", "Gambit", "Vista", "Pilgrim", "Ledger", "Beacon", "Mischief", "Rhapsody", "Charter", "Orchard", "Voyager", "Spire", "Verdict", "Kestrel"]


## Makes a random field. The first runner is the player's horse.
## Each entry: name, silk_id, silk_a, silk_b, coat_name, coat, points, mine.
static func make_field(count: int, rng: RandomNumberGenerator) -> Array:
	var field := []
	var used_names := {}
	var silk_order := range(SILKS.size())
	_shuffle(silk_order, rng)
	var used_colours := {}
	var si := 0
	for i in count:
		# a name that hasn't been used yet in this field
		var horse_name := ""
		while horse_name == "" or used_names.has(horse_name):
			horse_name = "%s %s" % [NAME_A[rng.randi() % NAME_A.size()], NAME_B[rng.randi() % NAME_B.size()]]
			if horse_name.get_slice(" ", 0) == horse_name.get_slice(" ", 1):
				horse_name = ""
		used_names[horse_name] = true
		# silks whose colour pair hasn't been used yet, so every runner looks different
		var silk: Array = SILKS[silk_order[si]]
		while used_colours.has(silk[1] + silk[2]) and si < silk_order.size() - 1:
			si += 1
			silk = SILKS[silk_order[si]]
		used_colours[silk[1] + silk[2]] = true
		si += 1
		var coat: Dictionary = COATS[rng.randi() % COATS.size()]
		field.append({
			"name": horse_name,
			"silk_id": silk[0],
			"silk_a": Color(silk[1]),
			"silk_b": Color(silk[2]),
			"coat_name": coat["name"],
			"coat": Color(coat["body"]),
			"points": Color(coat["points"]),
			"mine": i == 0,
		})
	return field


static func _shuffle(arr: Array, rng: RandomNumberGenerator) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = arr[i]
		arr[i] = arr[j]
		arr[j] = t
