#version 330 core

precision mediump float;
in vec3 normal_interp;  // Surface normal
in vec3 vertPos;       // Vertex position
in vec3 colorInterp;

uniform mat3 K_materials;
uniform mat3 I_light;

uniform int mode;   // Rendering mode
uniform float shininess; // Shininess
uniform vec3 light_pos; // Light position
uniform int custom_light_enabled;
uniform vec3 custom_light_pos;
uniform vec3 custom_light_diffuse;
uniform vec3 custom_light_specular;
uniform vec3 custom_light_ambient;
uniform int hdri_environment_enabled;
uniform vec3 hdri_environment_color;
uniform float hdri_environment_intensity;
uniform vec3 emissive_color;
uniform float emissive_strength;
uniform float u_alpha;
out vec4 fragColor;

void main() {
  vec3 N = normalize(normal_interp);
  vec3 L = normalize(light_pos - vertPos);
  vec3 R = reflect(-L, N);      // Reflected light vector
  vec3 V = normalize(-vertPos); // Vector to viewer

  float specAngle = max(dot(R, V), 0.0);
  float specular = pow(specAngle, shininess);
  vec3 g = vec3(max(dot(L, N), 0.0), specular, 1.0);
  vec3 rgb = 0.5*matrixCompMult(K_materials, I_light) * g + 0.5*colorInterp;

  if (custom_light_enabled != 0) {
    vec3 L2 = normalize(custom_light_pos - vertPos);
    vec3 R2 = reflect(-L2, N);
    float specAngle2 = max(dot(R2, V), 0.0);
    float specular2 = pow(specAngle2, shininess);
    vec3 g2 = vec3(max(dot(L2, N), 0.0), specular2, 1.0);
    mat3 I_custom = mat3(custom_light_diffuse, custom_light_specular, custom_light_ambient);
    rgb += 0.5 * matrixCompMult(K_materials, I_custom) * g2;
  }

  if (hdri_environment_enabled != 0) {
    rgb += K_materials[2] * hdri_environment_color * hdri_environment_intensity;
  }

  rgb += emissive_color * emissive_strength;

  fragColor = vec4(rgb, u_alpha);
}
