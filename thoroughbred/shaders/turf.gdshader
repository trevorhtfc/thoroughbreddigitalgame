// Mown-turf stripes for the track surface.
shader_type spatial;

uniform vec3 light_grass : source_color = vec3(0.27, 0.40, 0.17);
uniform vec3 dark_grass : source_color = vec3(0.22, 0.34, 0.14);
uniform float stripe_width = 12.0;

varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	float s = step(0.5, fract(world_pos.x / (stripe_width * 2.0)));
	vec3 col = mix(light_grass, dark_grass, s);
	col *= 0.94 + 0.12 * hash(floor(world_pos.xz * 4.0));   // a little grain
	ALBEDO = col;
	ROUGHNESS = 0.95;
	SPECULAR = 0.2;
}
