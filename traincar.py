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


class TrainCarAdd(bpy.types.Operator):
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
		min=0,
		description="Number of cars to generate"
	)
	velo = bpy.props.FloatVectorProperty(
		name="Velocity",
		subtype='VELOCITY',
		unit='VELOCITY',
		description="Initial Train Velocity"
	)

	derail = bpy.props.BoolProperty(
		name="Derail",
		default=False,
		description="Whether keyframe-controlled movement stops and rigid body physics takes over",
	)
	derail_collective = bpy.props.BoolProperty(
		name="All together",
		default=True,
		description="Do all cars lose acceleration and controlled movement at the same time?",
	)

	derail_at = bpy.props.EnumProperty(
		items=(
			('OBJ',"Object","Train derails at an object",'OBJECT_DATA',1),
			('LOC',"Location","Train derails at manually entered location",'AXIS_SIDE',2),
			('FRAME',"Frame","Train derails at specific frame",'TIME',3),
		),
		name='Derail At',
		description="What type of thing triggers a derailment",
	)

	derail_obj = bpy.props.StringProperty(
		name="Object",
		description="Derail train at this object's location"
	)
	derail_obj_type = bpy.props.EnumProperty(
		items=(
			('BOUND',"Bounds","Train derails as it is inside object's bounds",'MOD_SUBSURF',1),
			('LOC',"Center","Train derails when it is very close to object's center (location)",'MANIPUL',2),
		),
		name='Use Object',
		description="What type of thing triggers a derailment",
	)
	derail_loc = bpy.props.FloatVectorProperty(
		name="Derail Coords",
		subtype='XYZ',
		unit='NONE',
		description="Global coordinates to derailment"
	)

	derail_frame = bpy.props.IntProperty(
		name='Frame',
		default=10,
		description="Frame number for cars to stop controlled animation at"
	)
	derail_frame_spacing = bpy.props.FloatProperty(
		name='Spacing',
		default=1.0,
		description="Amount of frames between each subsequent car derailing after Frame above"
	)


	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.active_object.rigid_body is not None

	def execute(self, context):
		my_operation(
			spacing=self.spacing,
			amount=self.n,
			velo=self.velo,
			derail=self.derail,
			collectively=self.derail_collective,
			derail_type=self.derail_at,
			derail_val = self.derail_obj if self.derail_at == 'OBJ' else self.derail_loc if self.derail_at == 'LOC' else (self.derail_frame,self.derail_frame_spacing)
		)
		return {'FINISHED'}

	def draw(self,context):
		layout = self.layout
		col = layout.column(align=True)
		row = col.row(align=True)
		row.prop(self,'n')

		#positon
		col = layout.column(align=True)
		col.prop(self,'spacing')

		#velocity
		col = layout.column(align=True)
		col.prop(self,'velo')

		col = layout.column(align=True)
		col.prop(self,'derail')

		col = layout.column(align=True)
		col.enabled = self.derail
		row = col.row(align=True)
		row.prop(self,'derail_collective')
		row = col.row(align=True)
		row.prop(self,'derail_at')

		col = layout.column(align=True)
		col.enabled = self.derail
		if self.derail_at == 'OBJ':
			col.prop_search(self, 'derail_obj', context.scene, 'objects')
			col.prop(self,'derail_obj_type')
		elif self.derail_at == 'LOC':
			col.prop(self,'derail_loc')
		else:
			row = col.row(align=True)
			row.prop(self,'derail_frame')
			row = col.row(align=True)
			row.enabled = not self.derail_collective
			row.prop(self,'derail_frame_spacing')


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


def my_operation(spacing=(0,0,0),amount=1,velo=(0,0,0),derail=True,collectively=True,derail_type='FRAME',derail_val=None):

	for i in range(amount): # loop to do this for every new car
		start_frame = 1

		# handles to cars objects for constraint linking later
		current_car = bpy.context.active_object #car body should be active element for proper linking

		###
		# Linked Duplication
		###
		bpy.ops.object.duplicate_move_linked(
			TRANSFORM_OT_translate={
				'value': ( spacing[0], spacing[1], spacing[2] ),
				'constraint_orientation':'GLOBAL'
			} )
		bpy.ops.object.make_single_user(animation=True) # allows for separate keyframe times for traincar and constraints

		new_car = bpy.context.active_object # get next car object handle


		###
		# Motion Keyframing
		# note: bpy.context.scene.frame_current may be helpful for generic conversion
		###

		if not new_car.animation_data:
			new_car.animation_data_create()
		if not new_car.animation_data.action:
			new_car.animation_data.action = bpy.data.actions.new(new_car.name + "-Action")

		# find location curves if they already exist from parent object
		fx, fy, fz = (None,)*3
		kf_animated = None
		for fcurve in new_car.animation_data.action.fcurves:
			if fcurve.data_path == 'location':
				if fcurve.array_index == 0:
					fx = fcurve
				elif fcurve.array_index == 1:
					fy = fcurve
				elif fcurve.array_index == 2:
					fz = fcurve
			if fcurve.data_path == 'rigid_body.kinematic':
				kf_animated = fcurve

		if not fx:
			fx = new_car.animation_data.action.fcurves.new('location', index=0, action_group="train")
		if not fy:
			fy = new_car.animation_data.action.fcurves.new('location', index=1, action_group="train")
		if not fz:
			fz = new_car.animation_data.action.fcurves.new('location', index=2, action_group="train")
		if not kf_animated:
			kf_animated = new_car.animation_data.action.fcurves.new('rigid_body.kinematic',action_group="train")


		# FCurve settings
		fx.color_mode = 'AUTO_RGB'
		fy.color_mode = 'AUTO_RGB'
		fz.color_mode = 'AUTO_RGB'


		(sx,sy,sz) = new_car.location # save starting location from duplication

		# Initial keyframes
		kf_animated.keyframe_points.insert(start_frame,1).interpolation = 'CONSTANT' # "Animated" = True keyframed at frame 1
		fx.keyframe_points.insert(start_frame, sx).interpolation = 'LINEAR'
		fy.keyframe_points.insert(start_frame, sy).interpolation = 'LINEAR'
		fz.keyframe_points.insert(start_frame, sz).interpolation = 'LINEAR'


		if not derail:
			# set forever motion
			fx.extrapolation = 'LINEAR'
			fy.extrapolation = 'LINEAR'
			fz.extrapolation = 'LINEAR'

			# put in velocity
			fx.keyframe_points.insert(start_frame+1, sx+velo[0])
			fy.keyframe_points.insert(start_frame+1, sy+velo[1])
			fz.keyframe_points.insert(start_frame+1, sz+velo[2])
			return
		# Everything below must ONLY apply to rigid body physics and derailed trains

		if derail_type == 'FRAME':

			# Determine final on-rails frame for this car
			end_frame = derail_val[0]
			if not collectively:
				end_frame = derail_val[0] + (i+1)*derail_val[1]

			# delete any existing keyframes that would interfere with our motion here
			for key in kf_animated.keyframe_points:
				if key.co.x > start_frame and key.co.x <= end_frame+1:
					kf_animated.keyframe_points.remove(key) # @todo: will removing a key while looping bork the looping?
			for curve in (fx,fy,fz):
				for key in curve.keyframe_points:
					if key.co.x > start_frame and key.co.x <= end_frame:
						curve.keyframe_points.remove(key)

			# make our controlled keyframes
			kf_animated.keyframe_points.insert(end_frame+1, 0) # turn off keyframed motion, use rigid body phys now
			fx.keyframe_points.insert(end_frame, sx+velo[0]*end_frame)
			fy.keyframe_points.insert(end_frame, sy+velo[1]*end_frame)
			fz.keyframe_points.insert(end_frame, sz+velo[2]*end_frame)

		###
		# Reassign physics constraints links between cars
		#  special lil' handy bit to reassign any rigid body constraints
		#  that were copied to be between each car now
		###
		for obj in bpy.context.selected_objects:
			if obj.rigid_body_constraint != None:
				obj.rigid_body_constraint.object1 = current_car
				obj.rigid_body_constraint.object2 = new_car




def register():
	bpy.utils.register_class(TrainCarPanel)
	bpy.utils.register_class(TrainCarAdd)
def unregister():
	bpy.utils.unregister_class(TrainCarPanel)
	bpy.utils.unregister_class(TrainCarAdd)

if __name__ == "__main__":
	register()

