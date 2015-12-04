#!/usr/bin/env python
"""
materials.py -- Physically based shaders based on CynicatPro's tutorials on youtube

Copyright (c) 2015 Dan Panzarella <alsoelp@gmail.com>

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


import bpy
import itertools

"""
    Node group types: ShaderNodeTree, CompositorNodeTree, TextureNodeTree

    Node Socket types: NodeSocketVector, NodeSocketFloatUnsigned, NodeSocketVectorXYZ, NodeSocketVirtual, NodeSocketShader, NodeSocketVectorTranslation, NodeSocketIntFactor, NodeSocketBool, NodeSocketVectorEuler, NodeSocketInt, NodeSocketIntPercentage, NodeSocketFloatFactor, NodeSocketVectorAcceleration, NodeSocketVectorVelocity, NodeSocketString, NodeSocketVectorDirection, NodeSocketColor, NodeSocketIntUnsigned, NodeSocketFloatTime, NodeSocketFloatPercentage, NodeSocketFloatAngle, NodeSocketFloat
"""

def simplify_node(node):
    for sock in itertools.chain(node.inputs,node.outputs):
        if not sock.is_linked:
            sock.hide = True

class Group(object):
    """Wrapper for bpy group, to include input and output nodes automatically"""

    def __init__(self, name):
        super(Group, self).__init__()

        self._group = bpy.data.node_groups.new(name,'ShaderNodeTree')
        self.input_node = self._group.nodes.new('NodeGroupInput')
        self.output_node = self._group.nodes.new('NodeGroupOutput')

        self.input_node.location = (-350,0)
        self.output_node.location = (300,0)

    def __getattr__(self,name):
        return getattr(self._group,name)

    def __setattr__(self,name,value):
        if name in ['_group','input_node','output_node']:
            return super(Group,self).__setattr__(name,value)
        else:
            return setattr(self._group,name,value)
        


def make_fresnel():
    """ Includes properties for rim lighting, but not as good with glass
        (from about 7:50 mark on https://www.youtube.com/watch?v=FeH-g9bGz_4)
    """
    betterFresnel = Group('BetterFresnel')

    #setup group inputs
    roughness_in = betterFresnel.inputs.new('NodeSocketFloatFactor','Roughness')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    normal_in = betterFresnel.inputs.new('NodeSocketVector','Normal')
    normal_in.default_value = (0,0,0)
    normal_in.min_value = -1
    normal_in.max_value = 1
    ior_in = betterFresnel.inputs.new('NodeSocketFloatFactor','IOR')
    ior_in.default_value = 1.45
    ior_in.min_value = 0
    ior_in.max_value = 1000
    #group outputs
    fac_out = betterFresnel.outputs.new('NodeSocketFloatFactor','Fresnel')
    fac_out.default_value = 0
    fac_out.min_value = 0
    fac_out.max_value = 1
    facing_out = betterFresnel.outputs.new('NodeSocketFloat','Rim')
    facing_out.default_value = 0
    facing_out.min_value = 0
    facing_out.max_value = 1

    #group nodes
    bump = betterFresnel.nodes.new('ShaderNodeBump')
    geo = betterFresnel.nodes.new('ShaderNodeNewGeometry')
    mix = betterFresnel.nodes.new('ShaderNodeMixRGB')
    fresnel = betterFresnel.nodes.new('ShaderNodeFresnel')
    weight = betterFresnel.nodes.new('ShaderNodeLayerWeight')
    pow = betterFresnel.nodes.new('ShaderNodeMath')

    #connect 'em all
    betterFresnel.links.new(betterFresnel.input_node.outputs['Roughness'],mix.inputs['Fac'])
    betterFresnel.links.new(betterFresnel.input_node.outputs['Normal'],bump.inputs['Normal'])
    betterFresnel.links.new(betterFresnel.input_node.outputs['IOR'],fresnel.inputs['IOR'])
    betterFresnel.links.new(geo.outputs['Incoming'],mix.inputs['Color2'])
    betterFresnel.links.new(bump.outputs['Normal'],mix.inputs['Color1'])
    betterFresnel.links.new(mix.outputs['Color'],fresnel.inputs['Normal'])
    betterFresnel.links.new(fresnel.outputs['Fac'],betterFresnel.output_node.inputs['Fresnel'])
    betterFresnel.links.new(mix.outputs['Color'],weight.inputs['Normal'])
    betterFresnel.links.new(weight.outputs['Facing'],pow.inputs[0])
    betterFresnel.links.new(pow.outputs['Value'],betterFresnel.output_node.inputs['Rim'])


    bump.inputs['Strength'].default_value = 0
    pow.operation = 'POWER'
    pow.inputs[1].default_value = 2.5

    #prettify and arrange graph
    simplify_node(geo)
    simplify_node(bump)
    betterFresnel.input_node.location = (-564,203)
    bump.location = (-401,127)
    geo.location = (-433,79)
    mix.location = (-289,127)
    fresnel.location = (-150,147)
    weight.location = (-156,106)
    pow.location = (-51,108)
    betterFresnel.output_node.location = (72, 172)

    bump.hide = True
    mix.hide = True
    fresnel.hide = True
    weight.hide = True
    pow.hide = True

    return betterFresnel

def make_fresnel_f0():
    """ from https://www.youtube.com/watch?v=S2VLJZ_Zaz0 at about 10:20 min mark
        Where F0 is darkest value: (Fresnel - F0)/(1 - F0) + metallic rim shading

        to use: plug fresnel output into RGB Mix Fac, color1 is specular color, make c2 white
        then plug output color into glossy shader for a metal
    """
    betterFresnel = Group('BetterFresnel-F0')
    #setup group inputs
    roughness_in = betterFresnel.inputs.new('NodeSocketFloatFactor','Roughness')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    normal_in = betterFresnel.inputs.new('NodeSocketVector','Normal')
    normal_in.default_value = (0,0,0)
    normal_in.min_value = -1
    normal_in.max_value = 1
    ior_in = betterFresnel.inputs.new('NodeSocketFloatFactor','IOR')
    ior_in.default_value = 1.45
    ior_in.min_value = 0
    ior_in.max_value = 1000

    #group outputs
    fac_out = betterFresnel.outputs.new('NodeSocketFloatFactor','Fresnel')
    fac_out.default_value = 0
    fac_out.min_value = 0
    fac_out.max_value = 1
    facing_out = betterFresnel.outputs.new('NodeSocketFloat','Rim')
    facing_out.default_value = 0
    facing_out.min_value = 0
    facing_out.max_value = 1


    #group nodes
    bump = betterFresnel.nodes.new('ShaderNodeBump')
    geo = betterFresnel.nodes.new('ShaderNodeNewGeometry')
    mix = betterFresnel.nodes.new('ShaderNodeMixRGB')
    fresnel = betterFresnel.nodes.new('ShaderNodeFresnel')
    f0 = betterFresnel.nodes.new('ShaderNodeFresnel')
    sub = betterFresnel.nodes.new('ShaderNodeMath')
    sub2 = betterFresnel.nodes.new('ShaderNodeMath')
    div = betterFresnel.nodes.new('ShaderNodeMath')
    weight = betterFresnel.nodes.new('ShaderNodeLayerWeight')
    pow = betterFresnel.nodes.new('ShaderNodeMath')


    sub.operation = 'SUBTRACT'
    sub2.operation = 'SUBTRACT'
    div.operation = 'DIVIDE'
    pow.operation = 'POWER'

    #connect 'em all
    betterFresnel.links.new(betterFresnel.input_node.outputs['Roughness'],mix.inputs['Fac'])
    betterFresnel.links.new(betterFresnel.input_node.outputs['Normal'],bump.inputs['Normal'])
    betterFresnel.links.new(betterFresnel.input_node.outputs['IOR'],fresnel.inputs['IOR'])
    betterFresnel.links.new(geo.outputs['Incoming'],mix.inputs['Color2'])
    betterFresnel.links.new(bump.outputs['Normal'],mix.inputs['Color1'])
    betterFresnel.links.new(mix.outputs['Color'],fresnel.inputs['Normal'])
    betterFresnel.links.new(geo.outputs['Incoming'],f0.inputs['Normal'])
    betterFresnel.links.new(betterFresnel.input_node.outputs['IOR'],f0.inputs['IOR'])
    betterFresnel.links.new(fresnel.outputs['Fac'],sub.inputs[0])
    betterFresnel.links.new(f0.outputs['Fac'],sub.inputs[1])
    betterFresnel.links.new(f0.outputs['Fac'],sub2.inputs[1])
    betterFresnel.links.new(sub.outputs['Value'],div.inputs[0])
    betterFresnel.links.new(sub2.outputs['Value'],div.inputs[1])
    betterFresnel.links.new(mix.outputs['Color'],weight.inputs['Normal'])
    betterFresnel.links.new(weight.outputs['Facing'],pow.inputs[0])
    betterFresnel.links.new(div.outputs['Value'],betterFresnel.output_node.inputs['Fresnel'])
    betterFresnel.links.new(pow.outputs['Value'],betterFresnel.output_node.inputs['Rim'])



    bump.inputs['Strength'].default_value = 0
    sub2.inputs[0].default_value = 1
    pow.inputs[1].default_value = 2.5
    f0.label = "F0"


    #prettify and arrange graph
    simplify_node(geo)
    simplify_node(bump)
    betterFresnel.input_node.location = (-564,203)
    bump.location = (-401,127)
    geo.location = (-433,79)
    mix.location = (-289,127)
    fresnel.location = (-150,147)
    f0.location = (-150,103)
    weight.location = (-145,51)
    pow.location = (-25,45)
    sub.location = (-31,142)
    sub2.location = (-28,104)
    div.location = (98,121)
    betterFresnel.output_node.location = (250, 137)

    bump.hide = True
    mix.hide = True
    fresnel.hide = True
    f0.hide = True
    weight.hide = True
    pow.hide = True
    sub.hide = True
    sub2.hide = True
    div.hide = True

    return betterFresnel


def make_reflection_ior():
    """Can be added to basically make a clear coat"""
    reflect = Group('Reflection IOR')

    reflect.inputs.new('NodeSocketShader','Shader')
    reflect.outputs.new('NodeSocketShader','Shader')
    #setup group inputs
    roughness_in = reflect.inputs.new('NodeSocketFloatFactor','Roughness')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    ior_in = reflect.inputs.new('NodeSocketFloatFactor','IOR')
    ior_in.default_value = 1.45
    ior_in.min_value = 0
    ior_in.max_value = 1000
    normal_in = reflect.inputs.new('NodeSocketVector','Normal')
    normal_in.default_value = (0,0,0)
    normal_in.min_value = -1
    normal_in.max_value = 1


    gloss = reflect.nodes.new('ShaderNodeBsdfGlossy')
    mix = reflect.nodes.new('ShaderNodeMixShader')
    fresnel = reflect.nodes.new('ShaderNodeGroup')

    fresnel.node_tree = bpy.data.node_groups['BetterFresnel']

    reflect.links.new(reflect.input_node.outputs['Shader'],mix.inputs[1])
    reflect.links.new(reflect.input_node.outputs['Roughness'],fresnel.inputs['Roughness'])
    reflect.links.new(reflect.input_node.outputs['IOR'],fresnel.inputs['IOR'])    
    reflect.links.new(reflect.input_node.outputs['Normal'],fresnel.inputs['Normal'])
    reflect.links.new(reflect.input_node.outputs['Roughness'],gloss.inputs['Roughness'])    
    reflect.links.new(reflect.input_node.outputs['Normal'],gloss.inputs['Normal'])
    reflect.links.new(gloss.outputs['BSDF'],mix.inputs[2])
    reflect.links.new(mix.outputs['Shader'],reflect.output_node.inputs['Shader'])
    reflect.links.new(fresnel.outputs['Fresnel'],mix.inputs['Fac'])

def make_reflection():
    """ Adds less-physically correct, but nice, specular setting
        from https://www.youtube.com/watch?v=S2VLJZ_Zaz0 about 14min mark
    """

    reflect = Group('Reflection')

    reflect.inputs.new('NodeSocketShader','Shader')
    reflect.outputs.new('NodeSocketShader','Shader')
    #setup group inputs
    roughness_in = reflect.inputs.new('NodeSocketFloatFactor','Roughness')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    roughness_in = reflect.inputs.new('NodeSocketFloatFactor','Specular')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    normal_in = reflect.inputs.new('NodeSocketVector','Normal')
    normal_in.default_value = (0,0,0)
    normal_in.min_value = -1
    normal_in.max_value = 1


    gloss = reflect.nodes.new('ShaderNodeBsdfGlossy')
    mixcolor = reflect.nodes.new('ShaderNodeMixRGB')
    mix = reflect.nodes.new('ShaderNodeMixShader')
    fresnel = reflect.nodes.new('ShaderNodeGroup')

    fresnel.node_tree = bpy.data.node_groups['BetterFresnel-F0']

    reflect.links.new(reflect.input_node.outputs['Shader'],mix.inputs[1])
    reflect.links.new(reflect.input_node.outputs['Roughness'],fresnel.inputs['Roughness'])
    reflect.links.new(reflect.input_node.outputs['Normal'],fresnel.inputs['Normal'])
    reflect.links.new(reflect.input_node.outputs['Roughness'],gloss.inputs['Roughness'])    
    reflect.links.new(reflect.input_node.outputs['Normal'],gloss.inputs['Normal'])
    reflect.links.new(reflect.input_node.outputs['Specular'],mixcolor.inputs['Color1'])
    reflect.links.new(fresnel.outputs['Fresnel'],mixcolor.inputs['Fac'])
    reflect.links.new(mixcolor.outputs['Color'],mix.inputs['Fac'])
    reflect.links.new(gloss.outputs['BSDF'],mix.inputs[2])
    reflect.links.new(mix.outputs['Shader'],reflect.output_node.inputs['Shader'])

    gloss.inputs['Color'].default_value = (1,1,1,1)
    mixcolor.inputs['Color2'].default_value = (1,1,1,1)


def make_metal_basic():
    """ Basically just fresnel and glossy. Does not have rim lighting.
        From early point (up to about 6 min mark) on https://www.youtube.com/watch?v=FeH-g9bGz_4
    """

    metal = Group('Metal Basic')

    metal.outputs.new('NodeSocketShader','BSDF')
    metal.inputs.new('NodeSocketColor','Color')
    #setup group inputs
    roughness_in = metal.inputs.new('NodeSocketFloatFactor','Roughness')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    ior_in = metal.inputs.new('NodeSocketFloatFactor','IOR')
    ior_in.default_value = 1.45
    ior_in.min_value = 0
    ior_in.max_value = 1000
    normal_in = metal.inputs.new('NodeSocketVector','Normal')
    normal_in.default_value = (0,0,0)
    normal_in.min_value = -1
    normal_in.max_value = 1

    gloss = metal.nodes.new('ShaderNodeBsdfGlossy')
    mix = metal.nodes.new('ShaderNodeMixRGB')
    fresnel = metal.nodes.new('ShaderNodeGroup')
    fresnel.node_tree = bpy.data.node_groups['BetterFresnel']

    metal.links.new(metal.input_node.outputs['Roughness'],fresnel.inputs['Roughness'])
    metal.links.new(metal.input_node.outputs['IOR'],fresnel.inputs['IOR'])    
    metal.links.new(metal.input_node.outputs['Normal'],fresnel.inputs['Normal'])
    metal.links.new(metal.input_node.outputs['Roughness'],gloss.inputs['Roughness'])    
    metal.links.new(metal.input_node.outputs['Normal'],gloss.inputs['Normal'])
    metal.links.new(metal.input_node.outputs['Color'],mix.inputs['Color1'])
    metal.links.new(fresnel.outputs['Fac'],mix.inputs['Fac'])
    metal.links.new(mix.outputs['Color'],gloss.inputs['Color'])
    metal.links.new(metal.output_node.inputs['BSDF'],gloss.outputs['BSDF'])

    mix.inputs['Color2'].default_value = (1,1,1,1)


def make_metal_adv():
    """ Includes rim lighting. From https://www.youtube.com/watch?v=FeH-g9bGz_4 
        after 6 min mark
    """

    metal = Group('Metal')

    metal.outputs.new('NodeSocketShader','BSDF')
    metal.inputs.new('NodeSocketColor','Color')
    metal.inputs.new('NodeSocketColor','Rim')
    #setup group inputs
    roughness_in = metal.inputs.new('NodeSocketFloatFactor','Roughness')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    ior_in = metal.inputs.new('NodeSocketFloatFactor','IOR')
    ior_in.default_value = 1.45
    ior_in.min_value = 0
    ior_in.max_value = 1000
    normal_in = metal.inputs.new('NodeSocketVector','Normal')
    normal_in.default_value = (0,0,0)
    normal_in.min_value = -1
    normal_in.max_value = 1

    gloss = metal.nodes.new('ShaderNodeBsdfGlossy')
    mix = metal.nodes.new('ShaderNodeMixRGB')
    rim_mix = metal.nodes.new('ShaderNodeMixRGB')
    fresnel = metal.nodes.new('ShaderNodeGroup')
    fresnel.node_tree = bpy.data.node_groups['BetterFresnel-Metal']

    metal.links.new(metal.input_node.outputs['Roughness'],fresnel.inputs['Roughness'])
    metal.links.new(metal.input_node.outputs['IOR'],fresnel.inputs['IOR'])    
    metal.links.new(metal.input_node.outputs['Normal'],fresnel.inputs['Normal'])
    metal.links.new(metal.input_node.outputs['Roughness'],gloss.inputs['Roughness'])  
    metal.links.new(metal.input_node.outputs['Normal'],gloss.inputs['Normal'])
    metal.links.new(metal.input_node.outputs['Color'],rim_mix.inputs['Color1'])
    metal.links.new(metal.input_node.outputs['Rim'],rim_mix.inputs['Color2'])
    metal.links.new(fresnel.outputs['Rim'],rim_mix.inputs['Fac'])
    metal.links.new(fresnel.outputs['Fresnel'],mix.inputs['Fac'])
    metal.links.new(rim_mix.outputs['Color'],mix.inputs['Color1'])
    metal.links.new(mix.outputs['Color'],gloss.inputs['Color'])
    metal.links.new(metal.output_node.inputs['BSDF'],gloss.outputs['BSDF'])

    mix.inputs['Color2'].default_value = (1,1,1,1)


def make_metal_specular():
    """ Metal with rim shading, without IOR, using specular
        from https://www.youtube.com/watch?v=S2VLJZ_Zaz0 at 14:20
    """

    metal = Group('Metal-Specular')

    metal.outputs.new('NodeSocketShader','BSDF')
    metal.inputs.new('NodeSocketColor','Color')
    metal.inputs.new('NodeSocketColor','Rim')
    #setup group inputs
    roughness_in = metal.inputs.new('NodeSocketFloatFactor','Roughness')
    roughness_in.default_value = 0.01
    roughness_in.min_value = 0
    roughness_in.max_value = 1
    normal_in = metal.inputs.new('NodeSocketVector','Normal')
    normal_in.default_value = (0,0,0)
    normal_in.min_value = -1
    normal_in.max_value = 1

    gloss = metal.nodes.new('ShaderNodeBsdfGlossy')
    mix = metal.nodes.new('ShaderNodeMixRGB')
    rim_mix = metal.nodes.new('ShaderNodeMixRGB')
    fresnel = metal.nodes.new('ShaderNodeGroup')
    fresnel.node_tree = bpy.data.node_groups['BetterFresnel-Specular-Metal']

    metal.links.new(metal.input_node.outputs['Roughness'],fresnel.inputs['Roughness'])
    metal.links.new(metal.input_node.outputs['Normal'],fresnel.inputs['Normal'])
    metal.links.new(metal.input_node.outputs['Roughness'],gloss.inputs['Roughness'])  
    metal.links.new(metal.input_node.outputs['Normal'],gloss.inputs['Normal'])
    metal.links.new(metal.input_node.outputs['Color'],rim_mix.inputs['Color1'])
    metal.links.new(metal.input_node.outputs['Rim'],rim_mix.inputs['Color2'])
    metal.links.new(fresnel.outputs['Facing'],rim_mix.inputs['Fac'])
    metal.links.new(fresnel.outputs['Fac'],mix.inputs['Fac'])
    metal.links.new(rim_mix.outputs['Color'],mix.inputs['Color1'])
    metal.links.new(mix.outputs['Color'],gloss.inputs['Color'])
    metal.links.new(metal.output_node.inputs['BSDF'],gloss.outputs['BSDF'])

    mix.inputs['Color2'].default_value = (1,1,1,1)

def make_groups():
    make_fresnel()
    make_fresnel_f0()
    make_reflection()
    make_reflection_ior()
    make_metal_adv()
    make_metal_specular()


make_groups()
