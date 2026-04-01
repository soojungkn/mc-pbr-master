import torch
import numpy as np
from PIL import Image
import folder_paths
import random
import os

class MC_GrayscaleMapNode:
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=5))

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset": (["Manual", "Roughness (L)", "Height (R)", "Metallic (B)"],),
                "source_a": (["Luminance", "Red", "Green", "Blue", "Average"], {"default": "Red"}),
                "source_b": (["Luminance", "Red", "Green", "Blue", "Average"], {"default": "Luminance"}),
                "mix_ratio": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "black_point": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.001}),
                "gamma": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 9.99, "step": 0.01}),
                "white_point": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.001}),
                "brightness": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
                "contrast": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.01}),
                "invert": (["No", "Yes"],),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_map_and_preview"
    CATEGORY = "MC_PBR_Master/Map Generation"
    OUTPUT_NODE = True

    def apply_map_and_preview(self, image, preset, source_a, source_b, mix_ratio, black_point, gamma, white_point, brightness, contrast, invert):
        # --- Preview Image Saving (Send INPUT image to UI) ---
        preview_images = []
        if image is not None:
            # Save the FIRST image of the batch as preview
            # (Reason: Use input image as base for client-side Levels simulation)
            preview_img_tensor = image[0]
            i = 255. * preview_img_tensor.cpu().numpy()
            img_pil = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            # Resize for performance if too large (optional, but good for UI responsiveness)
            # max_dim = 512
            # if max(img_pil.size) > max_dim:
            #     img_pil.thumbnail((max_dim, max_dim))

            filename = f"{self.prefix_append}_{random.randint(0, 999999)}_preview.png"
            file_path = os.path.join(self.output_dir, filename)
            img_pil.save(file_path, compress_level=4)
            
            preview_images.append({
                "filename": filename,
                "subfolder": "",
                "type": self.type
            })

        # --- Original Levels Logic ---
        # 1. Channel Extraction
        if preset == "Manual":
            a_val = self.get_channel(image, source_a)
            b_val = self.get_channel(image, source_b)
            actual_ratio = mix_ratio
        else:
            target = {"Roughness (L)": "Luminance", "Height (R)": "Red", "Metallic (B)": "Blue"}[preset]
            a_val = self.get_channel(image, target)
            b_val = a_val
            actual_ratio = 0.0

        # 2. Mixing
        img = (a_val * (1.0 - actual_ratio)) + (b_val * actual_ratio)
        
        # 3. Levels (Exact calculation)
        # Black/White Remap
        range_val = max(white_point - black_point, 1e-5)
        img = torch.clamp((img - black_point) / range_val, 0.0, 1.0)
        
        # Gamma (Non-linear correction)
        img = torch.pow(img, 1.0 / max(gamma, 0.01))

        # 4. Post-processing
        img = (img - 0.5) * contrast + 0.5 + brightness
        if invert == "Yes":
            img = 1.0 - img
            
        img = torch.clamp(img, 0.0, 1.0)
        result_tensor = img.repeat(1, 1, 1, 3) # RGB 3-channel output

        return {
            "ui": {"images": preview_images},
            "result": (result_tensor,)
        }

    def get_channel(self, img, mode):
        if mode == "Red": return img[:,:,:,0:1]
        if mode == "Green": return img[:,:,:,1:2]
        if mode == "Blue": return img[:,:,:,2:3]
        if mode == "Average": return torch.mean(img, dim=-1, keepdim=True)
        # Luminance (Rec.709)
        return (0.2126 * img[:,:,:,0:1]) + (0.7152 * img[:,:,:,1:2]) + (0.0722 * img[:,:,:,2:3])

NODE_CLASS_MAPPINGS = { "MC_GrayscaleMap": MC_GrayscaleMapNode }
NODE_DISPLAY_NAME_MAPPINGS = { "MC_GrayscaleMap": "MC: Grayscale Map" }