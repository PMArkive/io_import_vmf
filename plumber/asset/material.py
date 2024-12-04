from typing import List

import bpy
from bpy.types import ShaderNode

from .utils import truncate_name
from ..plumber import Material, Texture, TextureRef


FORMAT_MAP = {
    ".tga": "TARGA_RAW",
    ".png": "PNG",
}

NODE_INPUT_SOCKET_MAP = {
    "Specular": "Specular IOR Level",
    "Emission": "Emission Color",
}


def import_texture(texture: Texture) -> None:
    format_ext = texture.format_ext()
    texture_name = truncate_name(texture.name() + format_ext)

    image_data = bpy.data.images.get(texture_name)
    if image_data is None:
        width = texture.width()
        height = texture.height()
        image_data = bpy.data.images.new(texture_name, width, height, alpha=True)
        image_data.file_format = FORMAT_MAP[format_ext]
        image_data.source = "FILE"
        bytes = texture.bytes()
        image_data.pack(data=bytes, data_len=len(bytes))
        image_data.alpha_mode = "CHANNEL_PACKED"


def import_material(material: Material) -> None:
    material_name = truncate_name(material.name())

    material_data = bpy.data.materials.get(material_name)
    if material_data is None:
        material_data = bpy.data.materials.new(material_name)
        material_data["path_id"] = material.name()

    material_data.use_nodes = True
    nt = material_data.node_tree
    nt.nodes.clear()

    out_node = nt.nodes.new("ShaderNodeOutputMaterial")
    out_node.location = (300, 0)

    built_data = material.data()
    texture_ext = material.texture_ext()

    for property, value in built_data.properties().items():
        setattr(material_data, property, resolve_value(value, texture_ext))

    built_nodes: List[ShaderNode] = []

    for node in built_data.nodes():
        built_node = nt.nodes.new(node.blender_id())
        built_node.location = node.position()

        for property, value in node.properties().items():
            setattr(built_node, property, resolve_value(value, texture_ext))

        for socket, value in node.socket_values().items():
            socket = resolve_input_socket(socket)
            built_node.inputs[socket].default_value = resolve_value(value, texture_ext)

        for socket, link in node.socket_links().items():
            target_node: ShaderNode = built_nodes[link.node_index()]
            target_socket = target_node.outputs[link.socket()]

            socket = resolve_input_socket(socket)
            nt.links.new(built_node.inputs[socket], target_socket)

        built_nodes.append(built_node)

    shader_node = built_nodes[-1]

    nt.links.new(shader_node.outputs["BSDF"], out_node.inputs["Surface"])

    for texture_name, color_space in built_data.texture_color_spaces().items():
        image_name = truncate_name(texture_name + texture_ext)
        image = bpy.data.images[image_name]
        image.colorspace_settings.name = color_space


def resolve_value(value, texture_ext: str):
    if isinstance(value, TextureRef):
        texture_name = truncate_name(value.path() + texture_ext)
        return bpy.data.images.get(texture_name)

    return value


def resolve_input_socket(socket: str):
    return NODE_INPUT_SOCKET_MAP.get(socket, socket)
