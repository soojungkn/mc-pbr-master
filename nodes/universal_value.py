import torch

class UniversalValueNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "value": ("FLOAT", {"default": 0.5, "min": -9999999.0, "max": 9999999.0, "step": 0.01, "display": "number"}),
                "min_value": ("FLOAT", {"default": 0.0, "min": -9999999.0, "max": 9999999.0, "step": 0.1, "display": "number"}),
                "max_value": ("FLOAT", {"default": 1.0, "min": -9999999.0, "max": 9999999.0, "step": 0.1, "display": "number"}),
                "step": ("FLOAT", {"default": 0.1, "min": 0.001, "max": 1000.0, "step": 0.001, "display": "number"}),
            },
        }

    # 아티스트용 심플 포트 구성
    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "process_value"
    CATEGORY = "MC_PBR_Master"

    def process_value(self, value, min_value, max_value, step):
        # 1. 안전한 범위 설정
        actual_min = min(min_value, max_value)
        actual_max = max(min_value, max_value)
        
        # 2. Clamping (범위 제한)
        clamped_value = max(actual_min, min(value, actual_max))
        
        # 3. Step 보정
        if step > 0:
            steps_count = round(clamped_value / step)
            final_value = steps_count * step
            # 다시 한번 범위 확인
            final_value = max(actual_min, min(final_value, actual_max))
        else:
            final_value = clamped_value

        # 부동소수점 오차 보정
        final_value = float(f"{final_value:.10g}")

        # 수치와 텍스트 두 가지 형태로 리턴
        return (final_value,)

NODE_CLASS_MAPPINGS = { "UniversalValue": UniversalValueNode }
NODE_DISPLAY_NAME_MAPPINGS = { "UniversalValue": "MC: Value Master" }