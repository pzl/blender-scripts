#!/usr/bin/env python
"""
traincar.py -- Adds action for extending Rigid Body traincar-like segments in blender

Copyright (c) 2016 Dan Panzarella <alsoelp@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
#GOOD_ICONS = 'PLUS','ZOOMIN','AUTO','LINKED','NEW','CONSTRAINT','MOD_ARRAY'

import bpy


class MyOperator(bpy.types.Operator):
	bl_idname = "object.traincar"
	bl_label = "Add Traincar"
	bl_options = {'REGISTER', 'UNDO'}

	spacing = bpy.props.FloatVectorProperty(
		name="Spacing",
		subtype='TRANSLATION',
		unit='LENGTH',
		description="Initial Spacing between cars"
	)
	n = bpy.props.IntProperty(
		name="Cars",
		default=1,
		description="Number of cars to generate"
	)
	kf = bpy.props.FloatProperty(
		name="Keyframes",
		default=3,
		description="Keyframe separation for delayed linkage animation"
	)
	velo = bpy.props.FloatVectorProperty(
		name="Velocity",
		subtype='VELOCITY',
		unit='VELOCITY',
		description="Initial Train Velocity"
	)


	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.rigid_body is not None

	def execute(self, context):
		my_operation(
			spacing=self.spacing,
			n=self.n,
			keyframes=self.kf,
			velo=self.velo
		)
		return {'FINISHED'}

	def draw(self,context):
		layout = self.layout
		col = layout.column(align=True)
		row = col.row(align=True)
		row.prop(self,'n')

		col = layout.column(align=True)
		row=col.row(align=True)
		row.prop(self,'kf')

		#positon
		col = layout.column(align=True)
		col.prop(self,'spacing')

		#velocity
		col = layout.column(align=True)
		col.prop(self,'velo')


class TrainCarPanel(bpy.types.Panel):
	bl_label = "Traincar"
	bl_idname = "OBJECT_PT_traincar"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"


	def draw(self, context):
		layout = self.layout
		col = layout.column(align=True)
		row = col.row(align=True)
		row.operator("object.traincar", text = "Add cars", icon='AUTO')


def my_operation(spacing=(0,0,0),n=1,keyframes=1,velo=(0,0,0)):


	for i in range(n): # loop to do this for every new car

		# handles to current and next cars for linking
		current_car = None
		new_car = None

		#find current traincar object
		current_car = next(obj for obj in bpy.context.selected_objects if obj.type != 'EMPTY')

		###
		# perform linked duplication
		###
		bpy.ops.object.duplicate_move_linked(
			TRANSFORM_OT_translate={
				'value': ( spacing[0], spacing[1], spacing[2] ),
				'constraint_orientation':'GLOBAL'
			} )
		bpy.ops.object.make_single_user(animation=True) # allows for separate keyframe times for traincar and constraints

		# find traincar object
		new_car = next(obj for obj in bpy.context.selected_objects if obj.type != 'EMPTY')


		###
		# Keyframe Traincar object itself for initial velocity
		# note: bpy.context.scene.frame_current may be helpful for generic conversion
		###

		# keyframe the "Animated" Rigid body setting
		new_car.rigid_body.kinematic = True
		new_car.keyframe_insert('rigid_body.kinematic',frame=1)
		new_car.rigid_body.kinematic = False
		new_car.keyframe_insert('rigid_body.kinematic',frame=3)

		# keyframe movement
		new_car.keyframe_insert('location',frame=1) # frame the location from duplication
		new_car.location.x += velo[0] #move according to initial velocity
		new_car.location.y += velo[1]
		new_car.location.z += velo[2]
		new_car.keyframe_insert('location',frame=2) # frame the accel
		new_car.location.x -= velo[0] #move back to starting position
		new_car.location.y -= velo[1]
		new_car.location.z -= velo[2]

		###
		# Reassign physics constraints links between cars
		###
		for obj in bpy.context.selected_objects:
			if obj.type == 'EMPTY':
				obj.rigid_body_constraint.object1 = current_car
				obj.rigid_body_constraint.object2 = new_car

				#space out constraint keyframe endings
				#this part is super specific to what I needed in one instance
				#and probably should be taken out for any generic or repeated use of this script
				obj.animation_data.action.fcurves[0].keyframe_points[1].co.x += keyframes


def register():
	bpy.utils.register_class(TrainCarPanel)
	bpy.utils.register_class(MyOperator)
def unregister():
	bpy.utils.unregister_class(TrainCarPanel)
	bpy.utils.unregister_class(MyOperator)

if __name__ == "__main__":
	register()

