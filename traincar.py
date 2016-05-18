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
		default='LOC',
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
		do_traincars(
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
		row = col.row(align=True)
		row.prop(self,'derail')

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
			row = col.row(align=True)
			row.enabled = False
			row.prop(self,'derail_obj_type')
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




def duplicate(spacing):
	current_car = bpy.context.active_object #car body should be active element for proper linking

	# Linked Duplication
	bpy.ops.object.duplicate_move_linked(
		TRANSFORM_OT_translate={
			'value': ( spacing[0], spacing[1], spacing[2] ),
			'constraint_orientation':'GLOBAL'
		} )
	bpy.ops.object.make_single_user(animation=True) # allows for separate keyframe times for traincar and constraints

	new_car = bpy.context.active_object # get next car object handle

	###
	# Reassign physics constraints links between cars
	#  special lil' handy bit to reassign any rigid body constraints
	#  that were copied to be between each car now
	###
	for obj in bpy.context.selected_objects:
		if obj.rigid_body_constraint != None:
			obj.rigid_body_constraint.object1 = current_car
			obj.rigid_body_constraint.object2 = new_car

	return (current_car,new_car)


def get_or_make_curves(car):
	if not car.animation_data:
		car.animation_data_create()
	if not car.animation_data.action:
		car.animation_data.action = bpy.data.actions.new(car.name + "-Action")

	# find location curves if they already exist from parent object
	fx, fy, fz = (None,)*3
	kf_animated = None
	for fcurve in car.animation_data.action.fcurves:
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
		fx = car.animation_data.action.fcurves.new('location', index=0, action_group="train")
	if not fy:
		fy = car.animation_data.action.fcurves.new('location', index=1, action_group="train")
	if not fz:
		fz = car.animation_data.action.fcurves.new('location', index=2, action_group="train")
	if not kf_animated:
		kf_animated = car.animation_data.action.fcurves.new('rigid_body.kinematic',action_group="train")

	# FCurve settings
	fx.color_mode = 'AUTO_RGB'
	fy.color_mode = 'AUTO_RGB'
	fz.color_mode = 'AUTO_RGB'

	return (fx,fy,fz,kf_animated)


def start_movement(start_position,start_frame,curves):
	(fx,fy,fz,kf_animated) = curves

	# Initial keyframes
	kf_animated.keyframe_points.insert(start_frame,1).interpolation = 'CONSTANT' # "Animated" = True keyframed at frame 1
	fx.keyframe_points.insert(start_frame, start_position[0]).interpolation = 'LINEAR'
	fy.keyframe_points.insert(start_frame, start_position[1]).interpolation = 'LINEAR'
	fz.keyframe_points.insert(start_frame, start_position[2]).interpolation = 'LINEAR'


def move_forever(start_position,start_frame,velocity,curves):
	(fx,fy,fz,kf_animated) = curves

	# set forever motion
	fx.extrapolation = 'LINEAR'
	fy.extrapolation = 'LINEAR'
	fz.extrapolation = 'LINEAR'

	# put in velocity
	fx.keyframe_points.insert( start_frame+1, start_position[0] + velocity[0] )
	fy.keyframe_points.insert( start_frame+1, start_position[1] + velocity[1] )
	fz.keyframe_points.insert( start_frame+1, start_position[2] + velocity[2] )


def find_collision_frame(car_n, end_frame, start_position, velocity, derail_type, derail_val, collectively):
	if derail_type == 'FRAME':
		# Determine final on-rails frame for this car
		return derail_val[0] if collectively else derail_val[0] + (car_n+1)*derail_val[1]

	# otherwise type is object or location


	# for collective crashes where we computed the collision frame already, don't recompute, just send it back
	if collectively and end_frame is not None:
		return end_frame

	# determine where we are crashing
	point = derail_val if derail_type == 'LOC' else bpy.context.scene.objects[derail_val].location if derail_val else None
	if not point:	# we don't have a location set yet so hold off
		return None


	# @todo: assumes will collide within 500 frames. "Magic" number beware
	# @todo: <= 2 blender units also magic number.
	for i in range(500):
		if abs( (start_position[0]+velocity[0]*i) - point[0] ) <= 2 and \
		   abs( (start_position[1]+velocity[1]*i) - point[1] ) <= 2 and \
		   abs( (start_position[2]+velocity[2]*i) - point[2] ) <= 2:
			return i

	return None # no collision found



def end_movement(start_frame, end_frame, start_position, velocity, curves):
	(fx,fy,fz,kf_animated) = curves

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
	fx.keyframe_points.insert(end_frame, start_position[0] + velocity[0] * end_frame)
	fy.keyframe_points.insert(end_frame, start_position[1] + velocity[1] * end_frame)
	fz.keyframe_points.insert(end_frame, start_position[2] + velocity[2] * end_frame)


def do_traincars(spacing=(0,0,0),amount=1,velo=(0,0,0),derail=True,collectively=True,derail_type='FRAME',derail_val=None):
	start_frame = 1 # note: bpy.context.scene.frame_current may be helpful in the future
	end_frame = None

	for i in range(amount): # loop to do this for every new car

		current_car, new_car = duplicate(spacing)

		# Motion Keyframing
		fx,fy,fz,kf_animated = get_or_make_curves(new_car)

		start_movement(new_car.location, start_frame, (fx,fy,fz,kf_animated) )

		if not derail:
			move_forever(new_car.location,start_frame,velo, (fx,fy,fz,kf_animated))
			continue
		#only derailing trains below

		end_frame = find_collision_frame(i,end_frame, new_car.location, velo, derail_type,derail_val, collectively)
		if end_frame is None: # info not set yet, or no collision found
			continue

		# Set final keyframes at crash time
		end_movement(start_frame, end_frame, new_car.location, velo, (fx,fy,fz,kf_animated))




def register():
	bpy.utils.register_class(TrainCarPanel)
	bpy.utils.register_class(TrainCarAdd)
def unregister():
	bpy.utils.unregister_class(TrainCarPanel)
	bpy.utils.unregister_class(TrainCarAdd)

if __name__ == "__main__":
	register()

