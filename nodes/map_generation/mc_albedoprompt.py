class MC_AlbedoPrompt:
    """
    Generates optimized prompts for PBR Albedo map generation based on selected AI model.
    """

    # Prompt presets for each model
    PROMPT_PRESETS = {
        "Nano Banana Pro / Imagen 4": "A high-resolution seamless PBR Albedo map of [Material Name], photorealistic, highly detailed flat diffuse color, orthographic top-down view, perfectly flat lighting, no shadows, no ambient occlusion, no specular highlights, 8k resolution, macro-surface detail, calibrated neutral exposure, cinematic realism, highly detailed texture surface.",

        "Flux.2 Pro": "Seamless 8k PBR Albedo map of [Material Name], top-down orthographic scan, flat diffuse color, uniform global illumination, zero shadows, no ambient occlusion, matte surface with no specular highlights, macro-detail, neutral calibrated exposure, professional digital asset, flat 2D texture.",

        "Reve": "High-resolution seamless texture map of [Material Name], Albedo pass only. Flat diffuse lighting, orthographic top-down view. Technical scan quality, 8k resolution, macro surface details. Strictly no lighting information, no baked-in shadows, no specular reflections. Neutral gray-card calibrated exposure, hyper-realistic material surface.",

        "Z-image": "High-resolution PBR Albedo map of [Material Name]. Orthographic top-down scan, seamless tiling texture, 8k. The lighting is perfectly flat global illumination with zero shadows and zero ambient occlusion. Pure diffuse color only, no specular highlights, no gloss. Macro-surface detail, neutral calibrated exposure, photorealistic flat scan, professional VFX asset, matte finish.",
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "material_name": ("STRING", {
                    "multiline": False,
                    "placeholder": "Enter material name (e.g., rusty metal, marble, brick)"
                }),
                "model": (list(cls.PROMPT_PRESETS.keys()), {
                    "default": "Nano Banana Pro / Imagen 4"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "MC_PBR_Master/Map Generation"

    def generate_prompt(self, material_name, model):
        # Get the prompt template for the selected model
        prompt_template = self.PROMPT_PRESETS.get(model, self.PROMPT_PRESETS["Nano Banana Pro / Imagen 4"])

        # Replace [Material Name] with the user's input
        prompt = prompt_template.replace("[Material Name]", material_name)

        return (prompt,)


NODE_CLASS_MAPPINGS = {
    "MC_AlbedoPrompt": MC_AlbedoPrompt
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MC_AlbedoPrompt": "MC: Albedo Prompt Engine"
}
