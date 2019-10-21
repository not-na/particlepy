#version 330 core

layout(points) in;
layout(triangle_strip, max_vertices = 4) out;

in VS_OUT {
    vec3 color;
} gs_in[];

out vec3 fColor;

uniform float pSize;

void main() {
    fColor = gs_in[0].color;

    gl_Position = gl_in[0].gl_Position + vec4(-pSize, -pSize, 0, 0);
    EmitVertex();

    gl_Position = gl_in[0].gl_Position + vec4(pSize, -pSize, 0, 0);
    EmitVertex();

    gl_Position = gl_in[0].gl_Position + vec4(-pSize, pSize, 0, 0);
    EmitVertex();

    gl_Position = gl_in[0].gl_Position + vec4(pSize, pSize, 0, 0);
    EmitVertex();

    EndPrimitive();
}
