import torch
import numpy as np
import cv2

class AOGeneratorNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "intensity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.1}),
                "blur_radius": ("INT", {"default": 3, "min": 1, "max": 21, "step": 2}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_ao"
    CATEGORY = "MC_PBR_Master/Map Generation"

    def generate_ao(self, image, intensity, blur_radius):
        img = image.cpu().numpy()[0]
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        laplacian = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
        ao = np.clip(1.0 - (laplacian * intensity), 0, 1)
        
        if blur_radius > 1:
            ao = cv2.GaussianBlur(ao, (blur_radius, blur_radius), 0)
            
        ao_rgb = np.stack([ao, ao, ao], axis=-1)
        return (torch.from_numpy(ao_rgb).unsqueeze(0),)