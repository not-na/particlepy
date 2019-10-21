#version 330 core
out vec4 FragColor;

in vec3 fColor;

void main()
{
    FragColor = vec4(fColor.r*0.5, fColor.g, fColor.b, 1.0);//vec4(fColor, 1.0);
}