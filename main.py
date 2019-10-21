#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  main.py
#  
#  Copyright 2019 notna <notna@apparat.org>
#  
#  This file is part of particlepy.
#
#  particlepy is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  particlepy is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with particlepy.  If not, see <http://www.gnu.org/licenses/>.
#
from ctypes import c_uint

import pyglet
from pyglet.gl import *

import pyshaders

import particlepy

SIM_HEIGHT = 32
SIM_WIDTH = 32

DISPLAY_SCALE = 16

GRAVITY_SCALE = 64  # Equals peak-to-peak gravity

SHADER_PIXEL_FRAG = "shaders/pixel_frag.glsl"
SHADER_PIXEL_VERT = "shaders/pixel_vert.glsl"
SHADER_PIXEL_GEO = "shaders/pixel_geo.glsl"


class ShaderObjectPlus(pyshaders.ShaderObject):
    @staticmethod
    def __alloc(cls, shader_type):
        sobj = super().__new__(cls)
        sobj.sid = c_uint(glCreateShader(shader_type))
        sobj.owned = True
        return sobj

    @classmethod
    def geometry(cls):
        return ShaderObjectPlus.__alloc(cls, GL_GEOMETRY_SHADER)

    def source_from_file(self, fname):
        with open(fname, "r") as f:
            self.source = f.read()


class PixelGroup(pyglet.graphics.Group):
    def __init__(self, parent=None):
        super().__init__(parent)

        logs = ""

        self.vert = ShaderObjectPlus.vertex()
        self.vert.source_from_file(SHADER_PIXEL_VERT)

        self.frag = ShaderObjectPlus.fragment()
        self.frag.source_from_file(SHADER_PIXEL_FRAG)

        self.geo = ShaderObjectPlus.geometry()
        self.geo.source_from_file(SHADER_PIXEL_GEO)

        for obj in [self.vert, self.frag, self.geo]:
            if obj.compile() is False:
                logs += obj.logs

        if len(logs) == 0:
            self.prog = pyshaders.ShaderProgram.new_program()
            self.prog.attach(self.vert, self.frag, self.geo)
            if not self.prog.link():
                raise pyshaders.ShaderCompilationError(self.prog.logs)
        else:
            raise pyshaders.ShaderCompilationError(logs)

    def set_state(self):
        self.prog.use()
        self.prog.uniforms.pSize = 1/(SIM_WIDTH+1)

    def unset_state(self):
        self.prog.clear()


class ParticleWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch = pyglet.graphics.Batch()

        glClearColor(0., 0., 0., 0.)

        glDisable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

        self.sim = particlepy.Simulation(SIM_WIDTH, SIM_HEIGHT)

        self.pixels = self.batch.add(SIM_WIDTH*SIM_HEIGHT, GL_POINTS, pyglet.graphics.OrderedGroup(0, PixelGroup()),
                                     "v2f",
                                     "c3f",
                                     )
        v = []
        c = []
        for x in range(SIM_WIDTH):
            for y in range(SIM_HEIGHT):
                c.extend([0, 255, 0])
                v.extend([((x+0.5)/SIM_WIDTH*2)-1, ((y+0.5)/SIM_HEIGHT*2)-1])
        self.pixels.vertices = v
        self.pixels.colors = c

        self.particles = self.batch.add(1, GL_POINTS, pyglet.graphics.OrderedGroup(1),
                                        "v2f",
                                        "c3B",
                                        )

        pyglet.clock.schedule_interval(self.update, 1/20.)

    def update(self, dt=None):
        self.sim.tick()
        print(f"Gravity: {self.sim.gravity[0]} {self.sim.gravity[1]}")

        c = []
        for x in range(SIM_WIDTH):
            for y in range(SIM_HEIGHT):
                if self.sim.get_pixel(x, y):
                    #c.extend([255, 255, 100])
                    c.extend([1.0, 1.0, 0.5])
                else:
                #    c.extend([0, 0, 0])
                    #c.extend([128, x, y])
                    c.extend([0.5, x/128., y/128.])

        for particle in self.sim.particles:
            idx = int((int(particle.x/particlepy.GRID_MULTIPLIER))*SIM_WIDTH+(int(particle.y/particlepy.GRID_MULTIPLIER)))*3
            c[idx:idx+3] = particle.c

        self.pixels.colors = c

        v = []
        c = []
        s = particlepy.GRID_MULTIPLIER/DISPLAY_SCALE
        for particle in self.sim.particles:
            c.extend([255, 0, 255])
            v.extend([particle.x/s+s/2, particle.y/s+s/2])
        self.particles.resize(len(self.sim.particles))
        self.particles.vertices = v
        self.particles.colors = c

    def on_draw(self):
        self.batch.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        width, height = self.get_size()
        self.sim.gravity = [
            ((x/width)-0.5)*GRAVITY_SCALE,
            ((y/height)-0.5)*GRAVITY_SCALE,
            self.sim.gravity[2],
        ]

    def set2d(self):
        glDisable(GL_LIGHTING)

        # To avoid accidental wireframe GUIs and fonts
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()


if __name__ == "__main__":
    window = ParticleWindow(
        caption="ParticlePy",
        width=SIM_WIDTH*DISPLAY_SCALE,
        height=SIM_HEIGHT*DISPLAY_SCALE,
        resizable=False,
        vsync=True,
    )

    pyglet.app.run()
