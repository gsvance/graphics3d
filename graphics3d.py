# graphics3d.py
"""A simple object-oriented 3d graphics library using parallel projection.

This module is a wrapper around Zelle's graphics.py library, which is a module
that provides a simple object-oriented two-dimensional graphics library for
novice programmers. Zelle's graphics.py is itself a wrapper around Python's
Tkinter library, which all of this depends on.

This module adds some additional bells and whistles to graphics.py in order to
create a rudimentary three-dimensional graphics engine that can draw points,
lines, triangles, and more in 3d space. I use parallel projection here, which
projects all of 3D space into a 2D plane assuming a camera position that views
the scene from "infinite distance" in much the same way that the "plane of the
sky" is often treated in astronomy.
"""

#__version__ = "0.1" # I can put a version number here if I want to

# Version updates could go here...

######################################################################
# Module imports

from graphics import *

import math

#import time, os, sys

# Apparently this import needs to be different for Python 2 vs Python 3
#try:
#	import tkinter as tk
#except ImportError:
#	import Tkinter as tk

######################################################################
# Global variables and functions

def make_pizza_polygon(*points):
	"""Given a list of three or more points in 3D space, make a 3D ploygon out
	of those points by cutting it up into trianglular pizza slices. The pizza
	slices will all be made to meet at the average position of the list of
	points. Important note: make sure that the points are given in order around
	the circumference of the polygon.
	"""
	
	assert len(points) >= 3, "Make pizza polygon needs 3 or more points"
	
	center = Vector(0, 0, 0)
	for pt in points:
		center = center + pt.toVector()
	pcenter = (center / float(len(points))).toPoint3d()
	
	slices = []
	for i in range(len(points)):
		ii = (i + 1) % len(points)
		slices.append(Triangle(points[i], points[ii], pcenter))
	
	return slices

######################################################################
# Vector object for 3d math

class Vector:
	"""Mathematical vector object for doing spatial calculations in 3D."""
	
	def __init__(self, x, y, z):
		self.x = float(x)
		self.y = float(y)
		self.z = float(z)
	
	def __repr__(self):
		return "Vector({}, {}, {})".format(self.x, self.y, self.z)
	
	def __neg__(self):
		return Vector(-self.x, -self.y, -self.z)
	
	def __add__(self, other):
		return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
	
	def __sub__(self, other):
		return self + (-other)
	
	def __rmul__(self, other):
		return self * other
	
	def __mul__(self, other):
		return Vector(other * self.x, other * self.y, other * self.z)
	
	def __div__(self, other): # Python 2
		return (1.0 / other) * self
	
	def __truediv__(self, other): # Python 3
		return (1.0 / other) * self
	
	def mag(self):
		"""Return the vector's magnitude."""
		return math.hypot(math.hypot(self.x, self.y), self.z)
	
	def unit(self):
		"""Return the vector rescaled to have a magnitude of 1."""
		return self / self.mag()
	
	def dot(self, other):
		"""Return the dot product of this vector with another vector."""
		return self.x * other.x + self.y * other.y + self.z * other.z
	
	def cross(self, other):
		"""Return the cross product of this vector with another vector."""
		return Vector(self.y * other.z - self.z * other.y,
			self.z * other.x - self.x * other.z,
			self.x * other.y - self.y * other.x)
	
	def copy(self):
		return Vector(self.x, self.y, self.z)
	
	def getX(self):
		return self.x
	
	def getY(self):
		return self.y
	
	def getZ(self):
		return self.z
	
	def toPoint3d(self):
		return Point3d(self.x, self.y, self.z)

######################################################################
# Graphics window class and related classes

class GraphWin3d(GraphWin):
	"""Toplevel window for displaying all sorts of 3d graphics."""
	
	def __init__(self, title="3D Graphics Window", width=300, height=300,
		autoflush=False):
		GraphWin.__init__(self, title, width, height, autoflush)
		self.cam = None
	
	def __repr__(self):
		if self.isClosed():
			return "<Closed GraphWin3d>"
		else:
			form = "GraphWin3d({}, width={}, height={}, autoflush={})"
			return form.format(repr(self.master.title()), self.getWidth(),
				self.getHeight(), self.autoflush)
	
	def setCoords(self, xcenter, ycenter, scale):
		"""Set coordinates on the window very carefully so as to not screw up
		the projections. The user can pass the x, y position on the projection
		plane where the camera should be centered, as well as a scale factor
		relative to the pixel size of the window.
		"""
		
		x1 = xcenter - 0.5 * self.width * scale
		y1 = ycenter + 0.5 * self.height * scale
		x2 = xcenter + 0.5 * self.width * scale
		y2 = ycenter - 0.5 * self.height * scale
		
		# Reverse the y values to avoid flipping that axis the wrong way
		
		self.trans = Transform(self.width, self.height, x1, y1, x2, y2)
		self.redraw()
	
	def setCamera(self, az_angle, alt_angle, roll_angle):
		"""Rotate the camera in three angles (degrees)."""
		self.cam = Camera(az_angle, alt_angle, roll_angle)
		self.redraw()
	
	def toProjection(self, x, y, z):
		if self.cam is None:
			return x, y, z
		else:
			return self.cam.project(x, y, z)
	
	def toInversion(self, xp, yp, zp):
		if self.cam is None:
			return xp, yp, zp
		else:
			return self.cam.invert(xp, yp, zp)
	
	def redraw(self):
		
		def depth(my_item):
			try:
				return my_item.getDepth() # draw 3d objects by their depth
			except AttributeError:
				return float("-inf") # always draw 2d objects on top
		
		for item in sorted(self.items, key=depth, reverse=True):
			item.undraw()
			item.draw(self)
		self.update()

class Camera:
	"""Internal class for 3D view rotations and parallel projections."""
	
	def __init__(self, az_angle, alt_angle, roll_angle):
		# The camera angle specified by 0, 0, 0 is as follows:
		#   - We are looking in the -x direction
		#   - To our right is the +y direction
		# The az_angle rotates us around in the xy plane from +x towards +y
		# The alt_angle rotates us upwards from the xy plane towards +z
		# The roll_angle rotates our view in a clockwise direction
		
		# Convert all angles from degrees to radians
		az = math.radians(az_angle)
		alt = math.radians(alt_angle)
		roll = math.radians(roll_angle)
		
		# Sines and cosines calculated exactly once
		sz = math.sin(az)
		cz = math.cos(az)
		sl = math.sin(alt)
		cl = math.cos(alt)
		sr = math.sin(roll)
		cr = math.cos(roll)
		
		# Initial unit vectors
		ux0 = Vector(0, 1, 0)
		uy0 = Vector(0, 0, -1)
		uz0 = Vector(-1, 0, 0)
		
		# First rotation (in azimuth)
		ux1 = cz * ux0 + sz * uz0
		uy1 = uy0.copy()
		uz1 = -sz * ux0 + cz * uz0
		
		# Second rotation (in altitude)
		ux2 = ux1.copy()
		uy2 = cl * uy1 + -sl * uz1
		uz2 = sl * uy1 + cl * uz1
		
		# Third roation (in roll) for final unit vectors
		self.ux = cr * ux2 + sr * uy2
		self.uy = -sr * ux2 + cr * uy2
		self.uz = uz2.copy()
	
	def project(self, x, y, z):
		# Return the projected (window) coordinates from x, y, z in 3d space
		# The projected z coordinate represents distance "into" the screen
		xyz = Vector(x, y, z)
		xp = xyz.dot(self.ux)
		yp = xyz.dot(self.uy)
		zp = xyz.dot(self.uz)
		return xp, yp, zp
	
	def invert(self, xp, yp, zp):
		# Invert the projection and return the x, y, z coordinates in 3d space
		xyz = xp * self.ux + yp * self.uy + zp * self.uz
		return xyz.x, xyz.y, xyz.z

######################################################################
# 3D graphics object classes

class GraphicsObject3d(GraphicsObject):
	"""Generic base class for drawable objects that exist in 3D space."""
	
	def move(self, dx, dy, dz):
		""" """
		
		self._move(dx, dy, dz)
		
		if self.canvas is not None and self.canvas.isOpen():
			
			cam = self.canvas.cam
			if cam is not None:
				xn, yn, zn = cam.toProjection(x + dx, y + dy, z + dz)
			else:
				xn = x + dx
				yn = y + dy
				zn = z + dz
			
			trans = self.canvas.trans
			if trans is not None:
				mv_x = (xn - x) / trans.xscale
				mv_y = -(yn - y) / trans.yscale
			else:
				mv_x = xn - x
				mv_y = yn - y
			
			self.canvas.move(self.id, mv_x, mv_y)
			if canvas.autoflush:
				_root.update()
	
	def getDepth(self):
		"""Return the projection depth of this 3d graphics object. This is the
		projected z coordinate, the distance this object is placed "into" the
		screen. Objects that return large values should be drawn prior to
		objects returning small values."""
		
		x, y, z = self._center3d()
		xp, yp, zp = self.canvas.toProjection(x, y, z)
		return zp
	
	def _center3d(self):
		"""Returns coordinates of a 3D "center point" of this object as an
		(x, y, z) tuple. This point will be used for determining the projection
		depth of this 3D graphics object.
		"""
		pass # must override in subclass

class Point3d(GraphicsObject3d):
	
	def __init__(self, x, y, z):
		GraphicsObject3d.__init__(self, ["outline", "fill"])
		self.setfill = self.setOutline
		self.x = float(x)
		self.y = float(y)
		self.z = float(z)
	
	def __repr__(self):
		return "Point3d({}, {}, {})".format(self.x, self.y, self.z)
	
	def _draw(self, canvas, options):
		xp, yp, zp = canvas.toProjection(self.x, self.y, self.z)
		x, y = canvas.toScreen(xp, yp)
		return canvas.create_rectangle(x, y, x + 1, y + 1, options)
	
	def _move(self, dx, dy, dz):
		self.x = self.x + dx
		self.y = self.y + dy
		self.z = self.z + dz
		
	def _center3d(self):
		return self.x, self.y, self.z
	
	def clone(self):
		other = Point3d(self.x, self.y, self.z)
		other.config = self.config.copy()
		return other
	
	def getX(self):
		return self.x
	
	def getY(self):
		return self.y
	
	def getZ(self):
		return self.z
	
	def toVector(self):
		return Vector(self.x, self.y, self.z)

class Line3d(GraphicsObject3d):
	
	def __init__(self, p1, p2):
		GraphicsObject3d.__init__(self, ["arrow", "fill", "width"])
		self.p1 = p1.clone()
		self.p2 = p2.clone()
		self.setFill(DEFAULT_CONFIG["outline"])
		self.setOutline = self.setFill
	
	def __repr__(self):
		return "Line3d({}, {})".format(repr(self.p1), repr(self.p2))
	
	def _draw(self, canvas, options):
		p1 = self.p1
		p2 = self.p2
		xp1, yp1, zp1 = canvas.toProjection(p1.x, p1.y, p1.z)
		xp2, yp2, zp2 = canvas.toProjection(p2.x, p2.y, p2.z)
		x1, y1 = canvas.toScreen(xp1, yp1)
		x2, y2 = canvas.toScreen(xp2, yp2)
		return canvas.create_line(x1, y1, x2, y2, options)
	
	def _move(self, dx, dy, dz):
		self.p1.move(dx, dy, dz)
		self.p2.move(dx, dy, dz)
	
	def _center3d(self):
		p1 = self.p1
		p2 = self.p2
		return 0.5 * (p1.x + p2.x), 0.5 * (p1.y + p2.y), 0.5 * (p1.z + p2.z)
	
	def clone(self):
		other = Line(self.p1, self.p2)
		other.config = self.config.copy()
		return other
	
	def getP1(self):
		return self.p1.clone()
	
	def getP2(self):
		return self.p2.clone()
	
	def getCenter(self):
		p1 = self.p1
		p2 = self.p2
		return Point3d(0.5 * (p1.x + p2.x), 0.5 * (p1.y + p2.y),
			0.5 * (p1.z + p2.z))
	
	def setArrow(self, option):
		if option not in ["first", "last", "both", "none"]:
			raise GraphicsError(BAD_OPTION)
		self._reconfig("arrow", option)

class Triangle(GraphicsObject3d):
	
	def __init__(self, p1, p2, p3):
		GraphicsObject3d.__init__(self, ["outline", "width", "fill"])
		self.p1 = p1.clone()
		self.p2 = p2.clone()
		self.p3 = p3.clone()
	
	def __repr__(self):
		return "Triangle({}, {}, {})".format(repr(self.p1), repr(self.p2),
			repr(self.p3))
	
	def clone(self):
		other = Polygon(self.p1, self.p2, self.p3)
		other.config = self.config.copy()
		return other
	
	def getP1(self):
		return self.p1.clone()
	
	def getP2(self):
		return self.p2.clone()
	
	def getP3(self):
		return self.p3.clone()
	
	def _move(self, dx, dy, dz):
		self.p1.move(dx, dy, dz)
		self.p2.move(dx, dy, dz)
		self.p3.move(dx, dy, dz)
	
	def _draw(self, canvas, options):
		p1 = self.p1
		p2 = self.p2
		p3 = self.p3
		xp1, yp1, zp1 = canvas.toProjection(p1.x, p1.y, p1.z)
		xp2, yp2, zp2 = canvas.toProjection(p2.x, p2.y, p2.z)
		xp3, yp3, zp3 = canvas.toProjection(p3.x, p3.y, p3.z)
		x1, y1 = canvas.toScreen(xp1, yp1)
		x2, y2 = canvas.toScreen(xp2, yp2)
		x3, y3 = canvas.toScreen(xp3, yp3)
		return canvas.create_polygon(x1, y1, x2, y2, x3, y3, options)
	
	def _center3d(self):
		v1 = self.p1.toVector()
		v2 = self.p2.toVector()
		v3 = self.p3.toVector()
		vcenter = (v1 + v2 + v3) / 3.0
		return vcenter.getX(), vcenter.getY(), vcenter.getZ()
	
	def getCenter(self):
		v1 = self.p1.toVector()
		v2 = self.p2.toVector()
		v3 = self.p3.toVector()
		vc = (v1 + v2 + v3) / 3.0
		return vc.toPoint3d()

######################################################################
# Testing for if this file is directly executed

def test():
	
	from random import randrange
	
	# Show me a cube!
	cube_win = GraphWin3d("Cube Rotation", 600, 600, autoflush=False)
	cube_win.setBackground("black")
	cube_win.setCoords(0, 0, 1.0)
	cube_win.setCamera(15, 30, 0)
	s = 280 / 2
	p1 = Point3d(+s, +s, +s)
	p2 = Point3d(-s, +s, +s)
	p3 = Point3d(+s, -s, +s)
	p4 = Point3d(-s, -s, +s)
	p5 = Point3d(+s, +s, -s)
	p6 = Point3d(-s, +s, -s)
	p7 = Point3d(+s, -s, -s)
	p8 = Point3d(-s, -s, -s)
	triangles = []
	triangles.extend(make_pizza_polygon(p1, p2, p4, p3))
	triangles.extend(make_pizza_polygon(p5, p6, p8, p7))
	triangles.extend(make_pizza_polygon(p1, p5, p7, p3))
	triangles.extend(make_pizza_polygon(p1, p5, p6, p2))
	triangles.extend(make_pizza_polygon(p6, p2, p4, p8))
	triangles.extend(make_pizza_polygon(p3, p4, p8, p7))
	for i in range(0, len(triangles), 4):
		rand_color = color_rgb(randrange(256), randrange(256), randrange(256))
		for j in range(4):
			triangles[i+j].setFill(rand_color)
			triangles[i+j].setOutline(rand_color)
			triangles[i+j].draw(cube_win)
	cube_win.redraw()
	update()
	cube_win.getMouse()
	for a in range(360):
		cube_win.setCamera(15 + a, 30, 0)
		update(45.)
	for a in range(90):
		cube_win.setCamera(15, 30 - a, 0)
		update(45.)
	for a in range(361):
		cube_win.setCamera(15, -60, -a)
		update(45.)
	cube_win.getMouse()
	cube_win.close()
	del p1, p2, p3, p4, p5, p6, p7, p8
	del triangles, cube_win
	
	# Show me an icosahedron!
	ico_win = GraphWin3d("Icosahedron Rotation", 600, 600, autoflush=False)
	ico_win.setBackground("black")
	ico_win.setCoords(0, 0, 1.0)
	ico_win.setCamera(0, 90, 0)
	s = 220.0 / 2
	phi = 0.5 * (1.0 + math.sqrt(5.0))
	vertices = []
	vertices.append(Point3d(0, +s, +s * phi))
	vertices.append(Point3d(0, -s, +s * phi))
	vertices.append(Point3d(0, +s, -s * phi))
	vertices.append(Point3d(0, -s, -s * phi))
	vertices.append(Point3d(+s, +s * phi, 0))
	vertices.append(Point3d(-s, +s * phi, 0))
	vertices.append(Point3d(+s, -s * phi, 0))
	vertices.append(Point3d(-s, -s * phi, 0))
	vertices.append(Point3d(+s * phi, 0, +s))
	vertices.append(Point3d(-s * phi, 0, +s))
	vertices.append(Point3d(+s * phi, 0, -s))
	vertices.append(Point3d(-s * phi, 0, -s))
	triangles = []
	for i in range(12):
		for j in range(i+1, 12):
			for k in range(j+1, 12):
				d_ij = (vertices[i].toVector() - vertices[j].toVector()).mag()
				d_ik = (vertices[i].toVector() - vertices[k].toVector()).mag()
				d_jk = (vertices[j].toVector() - vertices[k].toVector()).mag()
				if 1.99 * s < d_ij < 2.01 * s and 1.99 * s < d_ik < 2.01 * s \
					and 1.99 * s < d_jk < 2.01 * s:
					triangles.append(Triangle(vertices[i], vertices[j],
						vertices[k]))
	for tri in triangles:
		rand_color = color_rgb(randrange(256), randrange(256), randrange(256))
		tri.setFill(rand_color)
		tri.setOutline(rand_color)
		tri.draw(ico_win)
	ico_win.redraw()
	update()
	ico_win.getMouse()
	for a in range(360):
		ico_win.setCamera(0, 90, a)
		update(45.)
	for a in range(2 * 360):
		ico_win.setCamera(a, 90. - .25 * a, 0)
		update(45.)
	ico_win.getMouse()
	ico_win.close()

if __name__ == "__main__":
	test()

