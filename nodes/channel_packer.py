import torch
import numpy as np

class ChannelPackerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {
                "R": ("IMAGE",),
                "G": ("IMAGE",),
                "B": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "pack_channels"
    CATEGORY = "MC_PBR_Master"

    def pack_channels(self, R=None, G=None, B=None):
        active_input = next((img for img in [R, G, B] if img is not None), None)
        
        if active_input is None:
            return (torch.zeros((1, 64, 64, 3), dtype=torch.float32),)

        batch_size, height, width, _ = active_input.shape
        
        def process_channel(img_tensor):
            if img_tensor is not None:
                return img_tensor.cpu().numpy()[0][:, :, 0]
            else:
                return np.zeros((height, width), dtype=np.float32)

        r = process_channel(R)
        g = process_channel(G)
        b = process_channel(B)
        
        merged_rgb = np.stack([r, g, b], axis=-1)
        return (torch.from_numpy(merged_rgb).unsqueeze(0),)