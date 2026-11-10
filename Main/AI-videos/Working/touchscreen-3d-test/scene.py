"""LAYER: Engineer. Original cinematic touchscreen mechanism, built and rendered in Blender.
THE FLOW: enforce guard -> select GPU only -> construct model -> animate -> previews or frames.
Units and layer separation are illustrative. No external models, textures or captured imagery.
"""
from __future__ import annotations
import bpy,math,json,sys,time,hashlib
from pathlib import Path
from mathutils import Vector

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard

def material(name,color,metal=0,rough=.4,emission=0,transmission=0):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    node=mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Metallic'].default_value=metal
    node.inputs['Roughness'].default_value=rough
    node.inputs['Transmission Weight'].default_value=transmission
    node.inputs['IOR'].default_value=1.46
    if emission:
        node.inputs['Emission Color'].default_value=(*color,1)
        node.inputs['Emission Strength'].default_value=emission
    return mat

def box(name,location,scale,mat,bevel=.06):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object;obj.name=name;obj.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new('Machined edge','BEVEL');mod.width=bevel;mod.segments=5
        obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    obj.data.materials.append(mat)
    for face in obj.data.polygons:face.use_smooth=True
    return obj

def curve(name,points,mat,radius=.009):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=2
    spline=data.splines.new('POLY');spline.points.add(len(points)-1)
    for p,v in zip(spline.points,points):p.co=(*v,1)
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat)
    return obj

def key(obj,frame,location=None,scale=None):
    if location is not None:obj.location=location;obj.keyframe_insert(data_path='location',frame=frame)
    if scale is not None:obj.scale=scale;obj.keyframe_insert(data_path='scale',frame=frame)

def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def setup_gpu():
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.refresh_devices()
    candidates=[d for d in prefs.devices if d.type=='OPTIX' and '2060' in d.name]
    if not candidates:raise RuntimeError('RTX 2060 OptiX device unavailable; CPU fallback prohibited')
    for device in prefs.devices:device.use=device.id==candidates[0].id
    import _cycles
    _cycles.set_device_override('OPTIX')
    selected=[{'name':d.name,'type':d.type,'enabled':bool(d.use)} for d in prefs.devices]
    print('CLIPPING_GPU_SELECTION '+json.dumps(selected),flush=True)
    return selected

def build():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='GPU'
    scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.denoiser='OPTIX'
    scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.035
    scene.cycles.max_bounces=7;scene.cycles.transmission_bounces=5;scene.cycles.transparent_max_bounces=4
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
    scene.render.fps=30;scene.frame_start=1;scene.frame_end=240
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.045,.065,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.22
    metal=material('Graphite anodised frame',(.055,.065,.08),.85,.24)
    dark=material('Black ceramic display backing',(.008,.012,.02),.32,.3)
    silver=material('Sensor conductor silver',(.19,.24,.27),.82,.29)
    copper=material('Copper flex terminals',(.6,.25,.065),.78,.3)
    glass=material('Optical cover glass',(.82,.92,1),0,.065,transmission=.92)
    sensorbase=material('Magnified sensor substrate',(.035,.055,.065),.2,.22)
    gold=material('Illustrative field gold',(1,.55,.095),.18,.23,emission=2.0)
    active=material('Local capacitance change',(.10,.68,1),.05,.25,emission=2.7)
    skin=material('Original fingertip skin',(.55,.29,.19),0,.46)
    skin_node=skin.node_tree.nodes.get('Principled BSDF');skin_node.inputs['Subsurface Weight'].default_value=.07
    noise=skin.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=105;noise.inputs['Detail'].default_value=2
    bump=skin.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.014
    skin.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);skin.node_tree.links.new(bump.outputs['Normal'],skin_node.inputs['Normal'])
    box('Titanium chassis',(0,0,0),(7.4,14.8,.58),metal,.48)
    box('Inset bezel',(0,0,.305),(7.13,14.53,.13),dark,.42)
    box('Display panel',(0,0,.39),(6.85,14.1,.10),dark,.34)
    # The display pixels are enlarged for an explanatory macro shot.
    pixels=[material(f'Display colour {i}',c,.2,.34,emission=.12) for i,c in enumerate([(.08,.35,.7),(.08,.55,.32),(.6,.10,.065)])]
    for row in range(39):
        for column in range(3):
            mat=pixels[column]
            box(f'Display subpixel strip {row}-{column}',(-2.18+column*2.18,-6.65+row*.35,.457),(2.12,.29,.015),mat,.015)
    board=box('Sensor optical substrate',(0,0,.51),(6.83,14.08,.055),sensorbase,.30)
    # Alternate diamond pads and interconnecting traces are schematic, not a production layout.
    for ix in range(9):
        x=-2.92+ix*.73
        curve(f'Column trace {ix}',[(x,-6.8,.565),(x,6.8,.565)],silver,.014)
        for iy in range(18):
            y=-6.35+iy*.745
            pad=box(f'Electrode pad {ix:02d}-{iy:02d}',(x,y,.58),(.46,.46,.025),silver,.026)
            pad.rotation_euler.z=math.pi/4
    for iy in range(18):
        y=-6.35+iy*.745
        curve(f'Row trace {iy}',[(-3.15,y,.602),(3.15,y,.602)],copper,.009)
    cover=box('Protective glass',(0,0,.73),(6.96,14.24,.13),glass,.36)
    for frame,z in [(1,.73),(35,.73),(100,1.72),(240,1.72)]:key(cover,frame,(0,0,z))
    for side in [-1,1]:
        box(f'Volume control {side}',(side*3.73,2,.03),(.06,1.18,.15),metal,.04)
    box('Speaker recess',(0,6.52,.66),(1.45,.18,.028),dark,.07)
    box('Camera island',(0,6.42,.665),(1.65,.42,.045),dark,.19)
    for i in range(9):
        box(f'Edge contact {i}',(-2.8+i*.7,-7.12,.15),(.31,.14,.08),copper,.02)
    # Field curves live in a separate explanatory layer above the real sensor grid.
    for ix in range(9):
        for iy in range(10):
            x=-2.92+ix*.73;y=-4.95+iy*.745
            near=(x-.73)**2+(y+1.97)**2<1.35
            points=[(x-.29+.58*j/20,y,.64+.78*math.sin(math.pi*j/20)) for j in range(21)]
            obj=curve(f'Field arch {ix}-{iy}',points,active if near else gold,.008)
            # Scale about the sensor surface so fields remain anchored at their terminals.
            for vertex in obj.data.splines[0].points:vertex.co.z-=.64
            obj.location.z=.64
            for f,s in [(1,.001),(65,.001),(105,1),(150,1),(190,.48 if near else 1),(240,.48 if near else 1)]:key(obj,f,scale=(1,1,s))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=(.73,-1.97,5.5))
    finger=bpy.context.object;finger.name='Original stylised fingertip';finger.scale=(.91,2.9,.72)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finger.data.materials.append(skin);finger.rotation_euler.x=math.radians(19)
    for face in finger.data.polygons:face.use_smooth=True
    for frame,z in [(1,7.6),(85,7.6),(135,4.0),(190,3.0),(240,3.0)]:key(finger,frame,(.73,-.20,z))
    # A nail is a conforming keratin plate, not an ellipsoid intersecting the skin.
    nailmat=material('Natural translucent pink nail',(.44,.26,.205),0,.38)
    nailnode=nailmat.node_tree.nodes.get('Principled BSDF')
    nailnode.inputs['Coat Weight'].default_value=.12
    nailnode.inputs['Coat Roughness'].default_value=.3
    nailnode.inputs['Subsurface Weight'].default_value=.035
    vertices=[(0,-1.55,.72*math.sqrt(1-(-1.55/2.9)**2)+.027)]
    rings=10;segments=64
    for ring in range(1,rings+1):
        fraction=ring/rings
        for segment in range(segments):
            angle=2*math.pi*segment/segments
            c,s=math.cos(angle),math.sin(angle)
            x=.51*fraction*math.copysign(abs(c)**.7,c)
            y=-1.55+.95*fraction*math.copysign(abs(s)**.7,s)
            surface=.72*math.sqrt(max(.01,1-(x/.91)**2-(y/2.9)**2))
            z=surface+.011+.016*(1-fraction*fraction)
            vertices.append((x,y,z))
    faces=[]
    for segment in range(segments):faces.append((0,1+segment,1+(segment+1)%segments))
    for ring in range(rings-1):
        first=1+ring*segments;following=first+segments
        for segment in range(segments):
            nxt=(segment+1)%segments
            faces.append((first+segment,following+segment,following+nxt,first+nxt))
    mesh=bpy.data.meshes.new('Conforming rounded nail plate');mesh.from_pydata(vertices,[],faces);mesh.update()
    nail=bpy.data.objects.new('Fingernail anatomical plate',mesh);bpy.context.collection.objects.link(nail);nail.parent=finger
    nail.data.materials.append(nailmat)
    for face in nail.data.polygons:
        face.use_smooth=True
    solid=nail.modifiers.new('Keratin thickness','SOLIDIFY');solid.thickness=.008;solid.offset=-1
    bevel=nail.modifiers.new('Soft free edge','BEVEL');bevel.width=.004;bevel.segments=2
    floor=material('Studio slate',(.009,.013,.02),.15,.32)
    box('Studio floor',(0,0,-.45),(200,200,.1),floor,.01)
    for name,loc,power,size,color in [('Softbox key',(-8,-5,13),1750,10,(.75,.86,1)),('Warm rim',(7,7,9),2200,8,(1,.68,.35)),('Strip reflection',(-3,10,14),1600,6,(.8,.93,1)),('Front fill',(3,-12,7),700,8,(.45,.65,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.name=name;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.data.color=color;aim(light,(0,0,0))
    bpy.ops.object.camera_add(location=(9,-15,15));camera=bpy.context.object;camera.name='Macro dolly';scene.camera=camera;camera.data.lens=55
    camera.data.dof.use_dof=True;camera.data.dof.aperture_fstop=6.3
    bpy.ops.object.empty_add(location=(.4,-1,1));focus=bpy.context.object;focus.name='Sensor focal point';camera.data.dof.focus_object=focus
    for frame,loc,target in [(1,(9,-15,15),(0,0,.5)),(90,(7,-11,10),(.3,-1,.8)),(165,(5.5,-8.7,7.3),(.6,-1.5,1.25)),(240,(5.1,-8.1,6.8),(.6,-1.5,1.3))]:
        camera.location=loc;aim(camera,target);camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
    return scene

def main():
    require_guard(gpu=True)
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    mode=args[0] if args else 'preview'
    devices=setup_gpu();scene=build()
    PROJECT.mkdir(parents=True,exist_ok=True)
    scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'touchscreen.blend'))
    (PROJECT/'gpu-device.json').write_text(json.dumps({'devices':devices,'cycles_device':scene.cycles.device,'backend':'OPTIX','cpu_rendering_enabled':False,'samples':32,'threads':2},indent=2))
    folder=PROJECT/('previews' if mode=='preview' else 'benchmark' if mode=='benchmark' else 'frames');folder.mkdir(exist_ok=True)
    fingerprint=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if mode=='animation':
        marker=folder/'render-source.json'
        if marker.exists() and json.loads(marker.read_text())['sha256']!=fingerprint:
            raise RuntimeError('Existing animation frames belong to another scene version; preserve them in a different run folder')
        marker.write_text(json.dumps({'sha256':fingerprint,'samples':32,'width':1080,'height':1920,'fps':30}))
    scene.render.resolution_percentage=67 if mode=='preview' else 100
    if mode=='preview':scene.render.resolution_x=720;scene.render.resolution_y=1280;scene.render.resolution_percentage=100
    frames=[1,105,210] if mode=='preview' else [210] if mode=='benchmark' else range(1,241)
    times=[]
    for frame in frames:
        path=folder/f'{frame:04d}.png'
        if path.exists() and mode=='animation':continue
        scene.frame_set(frame);scene.render.filepath=str(path);start=time.monotonic()
        bpy.ops.render.render(write_still=True)
        elapsed=time.monotonic()-start;times.append({'frame':frame,'seconds':elapsed})
        (PROJECT/f'{mode}-timings.json').write_text(json.dumps(times,indent=2))
        print(f'CLIPPING_FRAME_DONE {frame} {elapsed:.3f}',flush=True)

if __name__=='__main__':main()
