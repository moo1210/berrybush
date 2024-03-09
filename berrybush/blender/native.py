# not a part of standard berrybush (see: https://github.com/moo1210/berrybush)
import warnings
import bpy
import gpu
import numpy as np
from mathutils import Matrix

from berrybush.blender.common import PropertyPanel
from berrybush.blender.render import MainBRRESRenderer


class NativeBlenderRender:
    def __init__(self):
        self.nativeRenderer = MainBRRESRenderer(False)

    def render(self, depsgraph, context=None):
        self.nativeRenderer.update(depsgraph, context)
        worldColor = np.array(bpy.context.scene.world.color[:3]) ** .4545
        fb: gpu.types.GPUFrameBuffer = gpu.state.active_framebuffer_get()
        fb.clear(color=(*worldColor, 0), depth=1)
        self.nativeRenderer.draw(Matrix(), Matrix())

        for i, (k, mat) in enumerate(self.nativeRenderer.materials.items()):
            nativeMat = NativeBlenderMaterial(self, mat.rawMat)
            nativeMat.generateNodesFromTex()

        # TODO: Context handling


class NativeBlenderMaterial:
    def __init__(self, render: NativeBlenderRender, mat: bpy.types.Material) -> None:
        self.render = render
        self.mat = mat

    def generateNodesFromTex(self):
        """Create a native Blender material for this material."""
        mat = self.mat

        mat.use_nodes = True
        blenderMatDiffuse = mat.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        blenderMatOutput = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(blenderMatDiffuse.outputs["BSDF"], blenderMatOutput.inputs["Surface"])

        for i, tex in enumerate(mat.brres.textures):
            if tex.activeImg is not None:
                blenderMatImage = mat.node_tree.nodes.new("ShaderNodeTexImage")
                blenderMatImage.image = tex.activeImg
                mat.node_tree.links.new(blenderMatDiffuse.inputs[0], blenderMatImage.outputs["Color"])

class NativeRenderOperation(bpy.types.Operator):
    bl_idname = "bress.native_render"
    bl_label = "Create Native Materials"

    def execute(self, context):
        render = NativeBlenderRender()
        depsgraph = context.evaluated_depsgraph_get()
        render.render(depsgraph)
        return {"FINISHED"}

class NativeMatPanel(PropertyPanel):
    bl_idname = "BRRES_PT_natmat"
    bl_label = "BRRES Settings"
    bl_context = "material"
    bl_options = set()

    @classmethod
    def poll(cls, context: bpy.types.Context):
        mat = context.material
        return mat is not None and context.engine != "BERRYBUSH" and not mat.grease_pencil

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        self.bl_options
        layout.operator("bress.native_render")
