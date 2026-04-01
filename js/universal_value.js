import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "MC.UniversalValueControl",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MC_UniversalValue") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const vWidget = this.widgets.find((w) => w.name === "value");
                const minWidget = this.widgets.find((w) => w.name === "min_value");
                const maxWidget = this.widgets.find((w) => w.name === "max_value");
                const stepWidget = this.widgets.find((w) => w.name === "step");

                // 드래그 거리를 임시 저장할 저장소
                let pixelAccumulator = 0;

                vWidget.mouse = function (e, pos, node) {
                    const s = parseFloat(stepWidget.value) || 0.1;
                    const minV = Math.min(minWidget.value, maxWidget.value);
                    const maxV = Math.max(minWidget.value, maxWidget.value);

                    if (e.type === "mousedown") {
                        pixelAccumulator = 0; // 클릭 시 초기화
                    } else if (e.type === "mousemove" && e.dragging) {
                        // 1. 마우스 이동 픽셀을 누적 (민감도 조절: 10px 이동 시 1 step 변화)
                        // 이 10이라는 숫자가 바로 "드래그 손맛"을 결정하는 고정값입니다.
                        pixelAccumulator += e.deltaX;
                        
                        const threshold = 10; // 10픽셀 움직일 때마다 1단계 변화

                        if (Math.abs(pixelAccumulator) >= threshold) {
                            // 몇 단계(step)를 움직여야 하는지 계산
                            const stepsToMove = Math.floor(pixelAccumulator / threshold);
                            let newValue = this.value + (stepsToMove * s);

                            // 범위 제한
                            newValue = Math.max(minV, Math.min(newValue, maxV));
                            
                            // 소수점 보정 및 할당
                            this.value = parseFloat(newValue.toFixed(4));
                            
                            // 사용한 만큼 누적치에서 차감 (잔여 픽셀 보존)
                            pixelAccumulator -= stepsToMove * threshold;

                            if (this.callback) this.callback(this.value);
                        }
                        return true; // 엔진의 기본 드래그 방지
                    }

                    // 화살표 영역(오른쪽 20px) 클릭 처리
                    if (e.type === "mousedown" && pos[0] > this.width - 20) {
                        const isUp = pos[1] < (this.last_y || 0) + (this.height || 20) / 2;
                        let val = this.value + (isUp ? s : -s);
                        this.value = Math.max(minV, Math.min(val, maxV));
                        if (this.callback) this.callback(this.value);
                        return true;
                    }
                };

                // 직접 숫자 입력 시 보정
                vWidget.callback = () => {
                    const s = parseFloat(stepWidget.value) || 0.1;
                    vWidget.value = Math.round(vWidget.value / s) * s;
                    this.setDirtyCanvas(true, true);
                };

                return r;
            };
        }
    },
});