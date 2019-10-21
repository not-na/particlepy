#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
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

import random
from dataclasses import dataclass

import numpy

GRID_MULTIPLIER = 256


@dataclass
class Particle(object):
    x: int
    y: int
    vx: int
    vy: int
    c: tuple

    __slots__ = (
        "x",  # X position in Particle-Space
        "y",  # Y position in Particle-Space
        "vx",  # X velocity in Particle-Space
        "vy",  # Y Velocity in Particle-Space
        "c",  # Color
    )


class Simulation(object):
    def __init__(self, width, height):
        if width % 32 != 0 or height % 32 != 0:
            raise ValueError("width and height must be multiples of 32!")

        self.gravity = [0, 0, 0]
        self.width = width
        self.height = height

        self.pwidth = width*GRID_MULTIPLIER-GRID_MULTIPLIER
        self.pheight = height*GRID_MULTIPLIER-GRID_MULTIPLIER

        self.grav_scale = 1
        self.bounce_scale = 0.5

        self.simtime = 0

        # One-dimensional array
        # Each pixel is represented by a single bit
        # 32 pixels are grouped together
        # 32bit numbers were chosen because the algorithm will run on a 32bit MPU
        # For a 32x32 display, every int represents a single line
        # For a 64x64 display, ints are ordered row-major, e.g. from left-to-right, then top-to-bottom
        # If a bit is set, something is there. It could be a fixed obstacle or a particle
        # No color or other information is stored to improve performance and simplify math
        self.bitmap = numpy.zeros((int(height*(width/32)),), dtype=numpy.uint32)

        self.particles = []

        self.init_particles()

    def init_particles(self):
        for x in range(32):
            for y in range(2):
                self.add_particle(Particle(x * GRID_MULTIPLIER, y * GRID_MULTIPLIER, 0, 0))

    def add_particle(self, particle):
        self.particles.append(particle)
        self.set_pixel(particle.x / GRID_MULTIPLIER, particle.y / GRID_MULTIPLIER)

    def get_pixel(self, x, y):
        # TODO: possibly adapt this code for sizes other than 32x32
        y = int(y)
        x = int(x)
        return self.bitmap[y] & (1 << (x % 32))

    def set_pixel(self, x, y):
        # TODO: possibly adapt this code for sizes other than 32x32
        y = int(y)
        x = int(x)
        self.bitmap[y] |= (1 << (x % 32))

    def clear_pixel(self, x, y):
        # TODO: possibly adapt this code for sizes other than 32x32
        y = int(y)
        x = int(x)
        self.bitmap[y] &= ~(1 << (x % 32))

    def tick(self):
        #for x in range(32):
        #    for y in range(32):
        #        print("#" if self.get_pixel(x, y) else " ", end="")
        #    print()
        # Internally, particles move around in a scaled-up grid from the graphics
        # This allows for higher precision and more realistic acceleration without using floats
        # Collisions are still only checked with the standard grid
        # For collision detection, whenever a particle "enters" a new pixel,
        # whether that pixel is occupied. If it is, if remains in its old pixel
        # and bounces based on its velocity.
        self.simtime += 1

        ax = self.gravity[0] * self.grav_scale
        ay = self.gravity[1] * self.grav_scale
        az = abs(self.gravity[2] * self.grav_scale)/8

        # Subtract az to re-add it randomly later
        ax -= az
        ay -= az
        raz = az*2.5  # Higher than two to produce a bias

        # TODO: evaluate if sorting particles bottom-to-top is reasonable

        # Update velocities of particles
        for particle in self.particles:
            # We add some slight random movements to prevent towers from building up
            # and even staying together when the direction changes
            particle.vx += ax + random.randint(0, raz)
            particle.vy += ay + random.randint(0, raz)

            # Limit velocity to grid multiplier to prevent clipping glitches
            # TODO: check if seperate axis checks are enough, to save a sqrt
            particle.vx = max(min(particle.vx, GRID_MULTIPLIER), -GRID_MULTIPLIER)
            particle.vy = max(min(particle.vy, GRID_MULTIPLIER), -GRID_MULTIPLIER)

        # Update position of particles
        # Particles are checked serially, which is not physically accurate
        # But its close enough that it won't be noticed by most
        # But first, define a helper function for bounces
        def bounce(n): return (-n)*self.bounce_scale

        for particle in self.particles:
            nx = particle.x + particle.vx
            ny = particle.y + particle.vy
            #print(f"x: {particle.x} y: {particle.y} vx: {particle.vx} vy: {particle.vy} nx: {nx} ny: {ny}")

            # Perform out-of-bounds check
            if nx < 0:
                #print("Xmin")
                nx = 0
                particle.vx = bounce(particle.vx)
            elif nx >= self.pwidth:
                #print("Xmax")
                nx = self.pwidth
                particle.vx = bounce(particle.vx)
            #print(f"nx/G: {nx} pwidth: {self.pwidth}")

            if ny < 0:
                #print("Ymin")
                ny = 0
                particle.vy = bounce(particle.vy)
            elif ny >= self.pheight:
                #print("Ymax")
                ny = self.pheight
                particle.vy = bounce(particle.vy)
            #print(f"ny/G: {ny} pheight: {self.pheight}")

            # Compare old and new pixel to see whether we need to check for collisions
            # idx stands for index. It combines both coordinates into a single number
            oidx = int(particle.y / GRID_MULTIPLIER) * self.width + int(particle.x / GRID_MULTIPLIER)
            nidx = int(ny / GRID_MULTIPLIER) * self.width + int(nx / GRID_MULTIPLIER)

            # Perform collision detection
            if oidx != nidx and self.get_pixel(nx/GRID_MULTIPLIER, ny/GRID_MULTIPLIER):
                #print(f"Collision: {nx} {ny} oidx: {oidx} nidx: {nidx}")
                # Position changed and there is a collision
                d = abs(nidx - oidx)  # "Distance" in offset in self.bitmap e.g. width*dy+dx

                # Single-axis collision
                if d == 1:  # Moved on the x axis
                    nx = particle.x
                    particle.vx = bounce(particle.vx)
                elif d == self.width:  # Moved on the y axis
                    ny = particle.y
                    particle.vy = bounce(particle.vy)
                # Diagonal collision
                # Skid along single axis starting with faster axis
                elif abs(particle.vx) >= abs(particle.vy):  # X is moving faster
                    if not self.get_pixel(nx / GRID_MULTIPLIER, particle.y / GRID_MULTIPLIER):
                        # Pixel along x axis is free
                        ny = particle.y  # Reset y position
                        particle.vy = bounce(particle.vy)
                    elif not self.get_pixel(particle.x / GRID_MULTIPLIER, ny / GRID_MULTIPLIER):
                        # Pixel along y axis is free
                        nx = particle.x  # Reset x position
                        particle.vx = bounce(particle.vx)
                    else:  # Both x and y neighbour occupied
                        # Reset both positions and bounce
                        nx = particle.x
                        ny = particle.y
                        particle.vx = bounce(particle.vx)
                        particle.vy = bounce(particle.vy)
                else:  # Y axis is moving faster
                    if not self.get_pixel(particle.x / GRID_MULTIPLIER, ny / GRID_MULTIPLIER):
                        # Pixel along y axis is free
                        nx = particle.x  # Reset x position
                        particle.vx = bounce(particle.vx)
                    elif not self.get_pixel(nx / GRID_MULTIPLIER, particle.y / GRID_MULTIPLIER):
                        # Pixel along x axis is free
                        ny = particle.y  # Reset y position
                        particle.vy = bounce(particle.vy)
                    else:  # Both x and y neighbour occupied
                        # Reset both positions and bounce
                        nx = particle.x
                        ny = particle.y
                        particle.vx = bounce(particle.vx)
                        particle.vy = bounce(particle.vy)

            # Move the particle
            # This runs always for every particle, even if it doesn't move
            self.clear_pixel(particle.x / GRID_MULTIPLIER, particle.y / GRID_MULTIPLIER)
            particle.x = nx
            particle.y = ny
            self.set_pixel(particle.x / GRID_MULTIPLIER, particle.y / GRID_MULTIPLIER)






