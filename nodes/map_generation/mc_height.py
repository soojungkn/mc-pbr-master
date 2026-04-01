import torch
import numpy as np
from PIL import Image
import folder_paths
import random
import os

class MC_HeightGen:
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=5))

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "channel": (["Luminance", "Red", "Green", "Blue"], {"default": "Luminance"}),
                "invert": (["No", "Yes"], {"default": "No"}),
                # JS UI와 연동되는 3총사 (필수)
                "black_point": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "white_point": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "gamma": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_height"
    CATEGORY = "MC_PBR_Master/Map Generation"
    OUTPUT_NODE = True

    def generate_height(self, image, channel, invert, black_point, white_point, gamma):
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

        # 1. Tensor -> Numpy (Batch 처리)
        # image shape: (Batch, H, W, Channel)
        input_images = image.cpu().numpy()
        out_batch = []

        for img in input_images:
            # 2. 채널 분리 (Channel Selector)
            if channel == "Red":
                # img[..., 0]은 Red 채널
                data = img[:, :, 0]
            elif channel == "Green":
                data = img[:, :, 1]
            elif channel == "Blue":
                data = img[:, :, 2]
            else: # Luminance (ITU-R BT.709 표준 가중치: 0.2126 R + 0.7152 G + 0.0722 B)
                data = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]

            # 3. Levels & Gamma Correction (핵심 수학 로직)
            # 0으로 나누기 방지용 엡실론
            epsilon = 1e-5
            
            # (Value - Black) / (White - Black)
            data = (data - black_point) / (white_point - black_point + epsilon)
            
            # Clip (0~1 사이로 자르기)
            data = np.clip(data, 0.0, 1.0)
            
            # Gamma Correction: Value ^ (1/Gamma)
            if gamma != 1.0:
                data = np.power(data, 1.0 / (gamma + epsilon))

            # 4. Invert (선택 사항)
            if invert == "Yes":
                data = 1.0 - data

            # 5. 차원 복구 (H, W) -> (H, W, 3) (RGB 형태로 복사)
            # ComfyUI는 흑백 이미지도 3채널로 보내는 것을 선호합니다.
            img_out = np.stack([data, data, data], axis=-1)
            out_batch.append(img_out)

        # Numpy -> Tensor
        result_tensor = torch.from_numpy(np.array(out_batch)).float()
        
        return {
            "ui": {"images": preview_images},
            "result": (result_tensor,)
        }