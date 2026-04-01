import torch
import numpy as np
import cv2

class ImageBlurNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "blur_type": (["Gaussian", "Box", "Median"],),
                "amount": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 100.0, "step": 0.1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_blur"
    CATEGORY = "MC_PBR_Master"

    def apply_blur(self, image, blur_type, amount):
        if amount < 0.1:
            return (image,)

        # 커널 사이즈는 항상 홀수여야 함
        kernel_size = int(amount)
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        img_np = image.cpu().numpy().copy()
        out_images = []

        for img in img_np:
            if blur_type == "Gaussian":
                res = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
            elif blur_type == "Box":
                res = cv2.boxFilter(img, -1, (kernel_size, kernel_size))
            elif blur_type == "Median":
                # 0~1 float를 0~255 uint8로 변환 후 연산
                res = cv2.medianBlur((img * 255).astype(np.uint8), kernel_size)
                res = res.astype(np.float32) / 255.0
            
            out_images.append(res)

        return (torch.from_numpy(np.stack(out_images)),)