import torch
import numpy as np
import cv2

class ImageSharpenNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "mode": (["UnsharpMask", "HighPass"],),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.05}),
                "radius": ("FLOAT", {"default": 1.0, "min": 1.0, "max": 20.0, "step": 0.1}),
                "threshold": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_sharpen"
    CATEGORY = "MC_PBR_Master"

    def apply_sharpen(self, image, mode, strength, radius, threshold):
        img_np = image.cpu().numpy().copy()
        out_images = []

        k_size = int(radius * 2) + 1
        if k_size % 2 == 0: k_size += 1

        for img in img_np:
            blurred = cv2.GaussianBlur(img, (k_size, k_size), radius)
            
            if mode == "UnsharpMask":
                diff = img - blurred
                mask = np.abs(diff) > threshold
                res = img + (diff * strength) * mask
            elif mode == "HighPass":
                res = (img - blurred) * strength + 0.5
            
            res = np.clip(res, 0.0, 1.0)
            out_images.append(res)

        return (torch.from_numpy(np.stack(out_images)),)