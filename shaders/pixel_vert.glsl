#version 330 core

layout (location = 0) in vec2 vert;
layout (location = 3) in vec3 inColor;

out VS_OUT {
    vec3 color;
} vs_out;

uniform float pSize;

void main() {
    gl_Position = vec4(vert.x, vert.y, 0, 1);
    vs_out.color = inColor;
}
