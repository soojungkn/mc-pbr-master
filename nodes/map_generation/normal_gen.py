import torch
import numpy as np
import cv2

class HeightToNormalNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "flip_y": (["No (OpenGL)", "Yes (DirectX)"],), 
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_normal"
    CATEGORY = "MC_PBR_Master/Map Generation"

    def generate_normal(self, image, strength, flip_y):
        img = image.cpu().numpy()[0]
        height = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        dx = cv2.Sobel(height, cv2.CV_32F, 1, 0, ksize=3)
        dy = cv2.Sobel(height, cv2.CV_32F, 0, 1, ksize=3)
        
        if flip_y == "Yes (DirectX)":
            dy = -dy
            
        dx *= strength
        dy *= strength
        dz = np.ones_like(height)
        
        norm = np.sqrt(dx**2 + dy**2 + dz**2)
        r = (dx / norm) * 0.5 + 0.5
        g = (dy / norm) * 0.5 + 0.5
        b = (dz / norm) * 0.5 + 0.5
        
        normal_rgb = np.stack([r, g, b], axis=-1)
        return (torch.from_numpy(normal_rgb).unsqueeze(0),)