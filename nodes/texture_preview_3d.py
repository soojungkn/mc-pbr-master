import torch
import numpy as np
from PIL import Image
import folder_paths
import os

class TexturePreview3DNode:
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_color": ("IMAGE",),
                "mesh_type": (["Sphere", "Cube", "Plane"],),
            },
            "optional": {
                "roughness": ("IMAGE",),
                "metallic": ("IMAGE",),
                "occlusion": ("IMAGE",),
                "normal": ("IMAGE",),
                "displacement": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("base_color", "roughness", "metallic", "occlusion", "normal", "displacement")
    FUNCTION = "preview_3d"
    OUTPUT_NODE = True
    CATEGORY = "MC_PBR_Master"

    def save_temp_image(self, tensor):
        i = 255. * tensor.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        filename = f"preview_{np.random.randint(0, 1000000)}.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        return filename

    def preview_3d(self, base_color, mesh_type, roughness=None, metallic=None, occlusion=None, normal=None, displacement=None):
        results = []
        fname = self.save_temp_image(base_color[0])
        results.append({"filename": fname, "type": self.type, "subfolder": "", "role": "base_color"})

        if roughness is not None:
            fname = self.save_temp_image(roughness[0])
            results.append({"filename": fname, "type": self.type, "subfolder": "", "role": "roughness"})

        if metallic is not None:
            fname = self.save_temp_image(metallic[0])
            results.append({"filename": fname, "type": self.type, "subfolder": "", "role": "metallic"})

        if occlusion is not None:
            fname = self.save_temp_image(occlusion[0])
            results.append({"filename": fname, "type": self.type, "subfolder": "", "role": "occlusion"})

        if normal is not None:
            fname = self.save_temp_image(normal[0])
            results.append({"filename": fname, "type": self.type, "subfolder": "", "role": "normal"})

        if displacement is not None:
            fname = self.save_temp_image(displacement[0])
            results.append({"filename": fname, "type": self.type, "subfolder": "", "role": "displacement"})

        return {
            "ui": {"texture_files": results, "mesh_type": mesh_type},
            "result": (base_color, roughness, metallic, occlusion, normal, displacement)
        }

NODE_CLASS_MAPPINGS = { "TexturePreview3D": TexturePreview3DNode }
NODE_DISPLAY_NAME_MAPPINGS = { "TexturePreview3D": "MC: 3D Texture Preview" }
