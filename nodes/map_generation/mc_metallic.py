import torch
import numpy as np
from PIL import Image
import folder_paths
import random
import os

class MC_MetallicGen:
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=5))

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                # 금속성은 보통 어두운 부분과 밝은 부분의 차이가 명확해야 합니다.
                "channel": (["Luminance", "Red", "Green", "Blue"], {"default": "Luminance"}),
                "invert": (["No", "Yes"], {"default": "No"}),
                # JS 연동
                "black_point": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "white_point": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "gamma": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_metallic"
    CATEGORY = "MC_PBR_Master/Map Generation"
    OUTPUT_NODE = True

    def generate_metallic(self, image, channel, invert, black_point, white_point, gamma):
        # --- Preview Image Saving (Send INPUT image to UI) ---
        preview_images = []
        if image is not None:
            preview_img_tensor = image[0]
            i = 255. * preview_img_tensor.cpu().numpy()
            img_pil = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            filename = f"{self.prefix_append}_{random.randint(0, 999999)}_preview.png"
            file_path = os.path.join(self.output_dir, filename)
            img_pil.save(file_path, compress_level=4)
            
            preview_images.append({
                "filename": filename,
                "subfolder": "",
                "type": self.type
            })

        input_images = image.cpu().numpy()
        out_batch = []

        for img in input_images:
            if channel == "Red":
                data = img[:, :, 0]
            elif channel == "Green":
                data = img[:, :, 1]
            elif channel == "Blue":
                data = img[:, :, 2]
            else:
                data = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]

            # Levels 로직
            epsilon = 1e-5
            data = (data - black_point) / (white_point - black_point + epsilon)
            data = np.clip(data, 0.0, 1.0)
            if gamma != 1.0:
                data = np.power(data, 1.0 / (gamma + epsilon))

            if invert == "Yes":
                data = 1.0 - data

            img_out = np.stack([data, data, data], axis=-1)
            out_batch.append(img_out)

        result_tensor = torch.from_numpy(np.array(out_batch)).float()
        return {
            "ui": {"images": preview_images},
            "result": (result_tensor,)
        }