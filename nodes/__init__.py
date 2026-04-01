from .map_generation import (
    MC_HeightGen,
    MC_RoughnessGen,
    MC_MetallicGen,
    HeightToNormalNode,
    AOGeneratorNode,
    MC_GrayscaleMapNode,
    MC_AlbedoPrompt
)
from .channel_packer import ChannelPackerNode
from .image_saver import PBRTextureExport
from .mc_image_blur import ImageBlurNode
from .mc_image_sharpen import ImageSharpenNode
from .mc_upscale import MC_ImageUpscaleNode
from .image_pass import ImagePreviewPassNode
from .seamless_checker import SeamlessCheckerNode
from .texture_preview_3d import TexturePreview3DNode
from .universal_value import UniversalValueNode

WEB_DIRECTORY = "./js"

NODE_CLASS_MAPPINGS = {
    "MC_AlbedoPrompt": MC_AlbedoPrompt,
    "MC_RoughnessGen": MC_RoughnessGen,
    "MC_MetallicGen": MC_MetallicGen,
    "MC_HeightGen": MC_HeightGen,
    "MC_HeightToNormal": HeightToNormalNode,
    "MC_AOGenerator": AOGeneratorNode,
    "MC_GrayscaleMap": MC_GrayscaleMapNode,
    "MC_ImageUpscale": MC_ImageUpscaleNode,
    "MC_SeamlessChecker": SeamlessCheckerNode,
    "MC_ImagePreviewPass": ImagePreviewPassNode,
    "MC_ImageBlur": ImageBlurNode,
    "MC_ImageSharpen": ImageSharpenNode,
    "MC_UniversalValue": UniversalValueNode,
    "MC_TexturePreview3D": TexturePreview3DNode,
    "MC_ChannelPacker": ChannelPackerNode,
    "MC_PBRTextureExport": PBRTextureExport,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MC_AlbedoPrompt": "MC: Albedo Prompt Engine",
    "MC_RoughnessGen": "MC: Roughness",
    "MC_MetallicGen": "MC: Metallic",
    "MC_HeightGen": "MC: Height Map",
    "MC_HeightToNormal": "MC: Height to Normal",
    "MC_AOGenerator": "MC: Ambient Occlusion",
    "MC_GrayscaleMap": "MC: Grayscale Map",
    "MC_ImageUpscale": "MC: AI Image Upscale",
    "MC_SeamlessChecker": "MC: Tile Checker",
    "MC_ImagePreviewPass": "MC: Image Preview Pass",
    "MC_ImageBlur": "MC: Image Blur",
    "MC_ImageSharpen": "MC: Image Sharpen",
    "MC_UniversalValue": "MC: Value Control",
    "MC_TexturePreview3D": "MC: 3D Texture Preview",
    "MC_ChannelPacker": "MC: RGB Channel Packer",
    "MC_PBRTextureExport": "MC: PBR Texture Export",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]