// Recolours the racehorse model per runner.
// The mask texture (assets/horses/silk_mask.png) marks areas of the original texture:
//   R = jockey silks, colour A (the orange hoops)
//   G = jockey silks, colour B (the blue/red hoops and the cap)
//   B = the horse itself (coat, mane, tail, legs) — tack, saddle cloth and jockey are left out
// Each area is repainted in the runner's colours, keeping the original light and shade.
shader_type spatial;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap;
uniform sampler2D mask_tex : hint_default_black, filter_linear;

uniform vec3 silk_a : source_color = vec3(1.0, 0.55, 0.1);
uniform vec3 silk_b : source_color = vec3(0.1, 0.3, 0.8);
uniform vec3 coat : source_color = vec3(0.48, 0.29, 0.16);     // body colour
uniform vec3 points : source_color = vec3(0.1, 0.08, 0.07);    // mane, tail, lower legs

// Median brightness in the original texture of: silk A, silk B, brown coat, dark points.
// Worked out when the mask was baked.
const vec4 REF = vec4(0.3529, 0.1439, 0.0537, 0.0076);

float lum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void fragment() {
	vec3 c = texture(albedo_tex, UV).rgb;
	vec4 m = texture(mask_tex, UV);
	float l = lum(c);
	vec3 col = c;
	col = mix(col, silk_a * clamp(l / REF.x, 0.35, 1.35), m.r);
	col = mix(col, silk_b * clamp(l / REF.y, 0.35, 1.35), m.g);
	// Horse: dark hair takes the points colour, brown hair the body colour, blended by brightness.
	float t = smoothstep(REF.w, REF.z, l);
	vec3 hair = mix(points, coat, t);
	float shade = clamp(l / mix(REF.w, REF.z, t), 0.45, 1.3);
	col = mix(col, hair * shade, m.b);
	ALBEDO = clamp(col, vec3(0.0), vec3(1.0));
	NORMAL_MAP = texture(normal_tex, UV).rgb;
	float silk = clamp(m.r + m.g, 0.0, 1.0);
	ROUGHNESS = mix(0.62, 0.38, silk);   // silks get a little satin sheen
	SPECULAR = 0.4;
}
