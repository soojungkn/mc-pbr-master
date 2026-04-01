import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
    name: "MC.PBR.LevelsUI",
    async beforeRegisterNodeDef(nodeType, nodeData) {

        const targetNodes = [
            "MC_GrayscaleMap",
            "MC_HeightGen",
            "MC_RoughnessGen",
            "MC_MetallicGen",
            "MC_Levels"
        ];

        if (!targetNodes.includes(nodeData.name)) return;

        // =====================================================================
        //  HELPER: Find Y where ALL widgets end (even "hidden" ones that
        //  ComfyUI still renders). We check every widget's last_y to be safe.
        // =====================================================================
        const getWidgetsBottom = (node) => {
            if (!node.widgets || node.widgets.length === 0) return 30;

            const WH = LiteGraph.NODE_WIDGET_HEIGHT || 20;
            let maxBottom = -1;

            // Check EVERY widget – do NOT skip hidden ones.
            // ComfyUI sometimes still renders widgets even when type="hidden".
            for (const w of node.widgets) {
                if (w.last_y != null && w.last_y > 0) {
                    maxBottom = Math.max(maxBottom, w.last_y + WH);
                }
            }
            if (maxBottom > 0) return maxBottom;

            // Fallback (first render, before last_y is set)
            let count = 0;
            for (const w of node.widgets) {
                if (w.type !== "hidden") count++;
            }
            // Also count "hidden" widgets that might still render
            // (black_point, gamma, white_point = up to 3 extra)
            const hiddenStillRendered = node.widgets.length - count;
            count += hiddenStillRendered;
            return (node.widgets_start_y || 30) + count * 24;
        };

        // =====================================================================
        //  NODE CREATION
        // =====================================================================
        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);

            // Try to hide level widgets (custom UI replaces them)
            for (const name of ["black_point", "gamma", "white_point"]) {
                const w = this.widgets?.find(v => v.name === name);
                if (w) {
                    w.type = "hidden";
                    w.computeSize = () => [0, -4];
                    w.hidden = true;
                }
            }

            // Internal state
            this._mc_img = new Image();
            this._mc_imgLoaded = false;
            this._mc_cache = null;
            this._mc_handle = null;  // "B" | "G" | "W" | null
            this._mc_val = null;
            this._mc_barY = 0;
            this._mc_barEnd = 0;

            // Intercept execution – DON'T call original to block ComfyUI preview
            this.onExecuted = function (message) {
                if (message?.images?.length > 0) {
                    const info = message.images[0];
                    const url = api.apiURL(
                        `/view?filename=${encodeURIComponent(info.filename)}` +
                        `&type=${info.type}&subfolder=${info.subfolder}` +
                        `&rand=${Math.random()}`
                    );
                    this._mc_img.src = url;
                    this._mc_img.onload = () => {
                        this._mc_imgLoaded = true;
                        this._mc_cache = null;
                        this.setDirtyCanvas(true);
                    };
                }
                this.imgs = null;
            };

            // Intercept channel widget changes → invalidate cache immediately
            // so the preview updates without re-queuing.
            setTimeout(() => {
                const chanW = this.widgets?.find(v => v.name === "channel");
                if (chanW) {
                    const origCB = chanW.callback;
                    chanW.callback = (...args) => {
                        this._mc_cache = null;
                        this.setDirtyCanvas(true);
                        origCB?.apply(chanW, args);
                    };
                }
            }, 0);

            // Global mouseup fallback
            this._mc_onGlobalMouseUp = () => {
                if (this._mc_handle) {
                    this._mc_handle = null;
                    this._mc_val = null;
                    if (app.canvas?.canvas) app.canvas.canvas.style.cursor = "default";
                    this.setDirtyCanvas(true);
                }
            };
            window.addEventListener("mouseup", this._mc_onGlobalMouseUp);

            const origRemoved = this.onRemoved;
            this.onRemoved = function () {
                window.removeEventListener("mouseup", this._mc_onGlobalMouseUp);
                origRemoved?.apply(this, arguments);
            };

            // Kick a re-draw so last_y gets populated
            setTimeout(() => this.setDirtyCanvas(true), 100);
        };

        // =====================================================================
        //  DRAW BACKGROUND – block ComfyUI default image preview
        // =====================================================================
        const origDrawBg = nodeType.prototype.onDrawBackground;
        nodeType.prototype.onDrawBackground = function (ctx) {
            this.imgs = null;
            origDrawBg?.apply(this, arguments);
        };

        // =====================================================================
        //  DRAW FOREGROUND
        // =====================================================================
        nodeType.prototype.onDrawForeground = function (ctx) {
            if (this.flags.collapsed) return;
            this.imgs = null; // extra safety

            const bW = this.widgets?.find(v => v.name === "black_point");
            const gW = this.widgets?.find(v => v.name === "gamma");
            const wW = this.widgets?.find(v => v.name === "white_point");
            if (!bW || !gW || !wW) return;

            const M = 10;                          // margin
            const NW = this.size[0];                 // node width
            const NH = this.size[1];                 // node height
            const DW = NW - M * 2;                   // drawable width

            // --- Layout: position bar BELOW all widgets ---
            const wBot = getWidgetsBottom(this);
            const barY = wBot + 10;
            const barH = 14;
            const triH = 10;
            const lblH = 12;
            const gap = 6;
            const prevY = barY + barH + triH + lblH + gap;

            // Store for mouse hit testing
            this._mc_barY = barY;
            this._mc_barEnd = barY + barH + triH + lblH;

            // ===== GRADIENT BAR =====
            const grad = ctx.createLinearGradient(M, 0, M + DW, 0);
            grad.addColorStop(0, "#000");
            grad.addColorStop(1, "#fff");
            ctx.fillStyle = grad;
            ctx.fillRect(M, barY, DW, barH);

            // ===== HANDLE POSITIONS =====
            const bX = M + bW.value * DW;
            const wX = M + wW.value * DW;
            const nG = (Math.log10(gW.value) + 1) / 2;
            const r = wW.value - bW.value;
            const gX = M + (bW.value + r * Math.max(0, Math.min(1, nG))) * DW;
            const tY = barY + barH;

            // ===== DRAW HANDLES =====
            const tri = (x, fill, stroke, label, on) => {
                ctx.fillStyle = fill;
                ctx.strokeStyle = stroke;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(x, tY);
                ctx.lineTo(x - 5, tY + triH);
                ctx.lineTo(x + 5, tY + triH);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
                ctx.fillStyle = on ? "#4caf50" : "#bbb";
                ctx.font = "bold 9px Arial";
                ctx.textAlign = "center";
                ctx.fillText(label, x, tY + triH + lblH);
            };

            tri(bX, "#111", "#666", "B", this._mc_handle === "B");
            tri(gX, "#888", "#bbb", "G", this._mc_handle === "G");
            tri(wX, "#eee", "#aaa", "W", this._mc_handle === "W");

            if (this._mc_handle && this._mc_val != null) {
                ctx.fillStyle = "#ccc";
                ctx.font = "10px monospace";
                ctx.textAlign = "center";
                ctx.fillText(this._mc_val.toFixed(3), M + DW / 2, barY - 3);
            }

            // ===== IMAGE PREVIEW (aspect-ratio preserved) =====
            const maxPH = Math.max(NH - prevY - M, 10);
            if (maxPH < 10) return;

            if (this._mc_imgLoaded) {
                // Calculate dimensions preserving aspect ratio
                const natW = this._mc_img.naturalWidth || 1;
                const natH = this._mc_img.naturalHeight || 1;
                const ratio = natW / natH;

                let drawW, drawH;
                if (DW / maxPH > ratio) {
                    // Height-limited
                    drawH = maxPH;
                    drawW = drawH * ratio;
                } else {
                    // Width-limited
                    drawW = DW;
                    drawH = drawW / ratio;
                }

                const drawX = M + (DW - drawW) / 2;  // center horizontally
                const drawY = prevY;

                // Auto-expand node to fit the preview
                const neededH = drawY + drawH + M;
                if (NH < neededH) this.size[1] = neededH;

                // Rebuild cached preview if needed
                const chanW = this.widgets?.find(v => v.name === "channel");
                const chanVal = chanW?.value ?? "Luminance"; // "Luminance"|"Red"|"Green"|"Blue"

                if (!this._mc_cache ||
                    this._mc_cache.width !== Math.round(drawW) ||
                    this._mc_cache.height !== Math.round(drawH) ||
                    this._mc_cache._chan !== chanVal ||
                    this._mc_handle) {

                    const c = document.createElement("canvas");
                    const tc = c.getContext("2d");
                    c.width = Math.round(drawW);
                    c.height = Math.round(drawH);
                    tc.drawImage(this._mc_img, 0, 0, c.width, c.height);

                    // Channel extraction + levels simulation
                    // Mirrors the Python backend logic exactly (Rec.709 for Luminance)
                    const id = tc.getImageData(0, 0, c.width, c.height);
                    const px = id.data;
                    const bk = bW.value, wh = wW.value;
                    const rng = Math.max(wh - bk, 1e-5);
                    const ig = 1.0 / Math.max(gW.value, 0.01);

                    for (let i = 0; i < px.length; i += 4) {
                        const r = px[i] / 255, g = px[i+1] / 255, b = px[i+2] / 255;

                        // Extract single channel value matching Python's get_channel()
                        let v;
                        if      (chanVal === "Red")   v = r;
                        else if (chanVal === "Green") v = g;
                        else if (chanVal === "Blue")  v = b;
                        else                          v = 0.2126*r + 0.7152*g + 0.0722*b; // Rec.709 Luminance

                        // Apply levels
                        v = Math.max(0, Math.min(1, (v - bk) / rng));
                        v = Math.pow(v, ig);

                        // Write as grayscale (single-channel display)
                        const out = v * 255;
                        px[i] = px[i+1] = px[i+2] = out;
                    }
                    tc.putImageData(id, 0, 0);
                    c._chan = chanVal; // tag for invalidation check
                    this._mc_cache = c;
                }

                ctx.drawImage(this._mc_cache, drawX, drawY);
            } else {
                // Placeholder
                const minH = prevY + 120 + M;
                if (NH < minH) this.size[1] = minH;

                ctx.fillStyle = "#1a1a1a";
                ctx.fillRect(M, prevY, DW, maxPH);
                ctx.fillStyle = "#555";
                ctx.font = "12px Arial";
                ctx.textAlign = "center";
                ctx.fillText("Queue to preview", M + DW / 2, prevY + maxPH / 2);
            }
        };

        // =====================================================================
        //  MOUSE DOWN
        // =====================================================================
        nodeType.prototype.onMouseDown = function (e, pos) {
            const barY = this._mc_barY;
            const barEnd = this._mc_barEnd;
            if (barY == null || pos[1] < barY || pos[1] > barEnd) return false;

            const M = 10;
            const DW = this.size[0] - M * 2;
            const x = (pos[0] - M) / DW;

            const bW = this.widgets.find(v => v.name === "black_point");
            const gW = this.widgets.find(v => v.name === "gamma");
            const wW = this.widgets.find(v => v.name === "white_point");
            if (!bW || !gW || !wW) return false;

            const nG = (Math.log10(gW.value) + 1) / 2;
            const gPos = bW.value + (wW.value - bW.value) * nG;
            const dB = Math.abs(x - bW.value);
            const dW = Math.abs(x - wW.value);
            const dG = Math.abs(x - gPos);
            const T = 0.15;

            if (dG < dB && dG < dW && dG < T) { this._mc_handle = "G"; this._mc_val = gW.value; }
            else if (dB < dW && dB < T) { this._mc_handle = "B"; this._mc_val = bW.value; }
            else if (dW < T) { this._mc_handle = "W"; this._mc_val = wW.value; }
            else return false;

            if (app.canvas?.canvas) app.canvas.canvas.style.cursor = "ew-resize";
            return true;
        };

        // =====================================================================
        //  MOUSE MOVE
        // =====================================================================
        nodeType.prototype.onMouseMove = function (e, pos) {
            if (!this._mc_handle) return false;

            // *** FIX: detect mouse release that LiteGraph missed ***
            // e.buttons === 0 means no buttons are pressed → drag ended
            if (e.buttons === 0) {
                this._mc_handle = null;
                this._mc_val = null;
                if (app.canvas?.canvas) app.canvas.canvas.style.cursor = "default";
                this.setDirtyCanvas(true);
                return false;
            }

            const M = 10;
            const DW = this.size[0] - M * 2;
            const x = Math.max(0, Math.min(1, (pos[0] - M) / DW));

            const bW = this.widgets.find(v => v.name === "black_point");
            const gW = this.widgets.find(v => v.name === "gamma");
            const wW = this.widgets.find(v => v.name === "white_point");

            if (this._mc_handle === "B") {
                bW.value = Math.min(x, wW.value - 0.01);
                this._mc_val = bW.value;
            } else if (this._mc_handle === "W") {
                wW.value = Math.max(x, bW.value + 0.01);
                this._mc_val = wW.value;
            } else if (this._mc_handle === "G") {
                const range = wW.value - bW.value;
                if (range > 0) {
                    let rel = Math.max(0.01, Math.min(0.99, (x - bW.value) / range));
                    gW.value = Math.pow(10, (rel * 2) - 1);
                    this._mc_val = gW.value;
                }
            }

            this._mc_cache = null;
            this.setDirtyCanvas(true);
            return true;
        };

        // =====================================================================
        //  MOUSE UP
        // =====================================================================
        nodeType.prototype.onMouseUp = function () {
            if (!this._mc_handle) return false;
            this._mc_handle = null;
            this._mc_val = null;
            if (app.canvas?.canvas) app.canvas.canvas.style.cursor = "default";
            this.setDirtyCanvas(true);
            return true;
        };

        // =====================================================================
        //  DOUBLE CLICK – reset nearest handle to default
        //  B → 0.0,  G → 1.0,  W → 1.0
        // =====================================================================
        nodeType.prototype.onDblClick = function (e, pos) {
            const barY = this._mc_barY;
            const barEnd = this._mc_barEnd;
            if (barY == null || pos[1] < barY || pos[1] > barEnd) return false;

            const M = 10;
            const DW = this.size[0] - M * 2;
            const x = (pos[0] - M) / DW;

            const bW = this.widgets.find(v => v.name === "black_point");
            const gW = this.widgets.find(v => v.name === "gamma");
            const wW = this.widgets.find(v => v.name === "white_point");
            if (!bW || !gW || !wW) return false;

            const nG = (Math.log10(gW.value) + 1) / 2;
            const gPos = bW.value + (wW.value - bW.value) * nG;
            const dB = Math.abs(x - bW.value);
            const dW = Math.abs(x - wW.value);
            const dG = Math.abs(x - gPos);
            const T = 0.15;

            if (dG < dB && dG < dW && dG < T) { gW.value = 1.0; }
            else if (dB < dW && dB < T) { bW.value = 0.0; }
            else if (dW < T) { wW.value = 1.0; }
            else return false;

            this._mc_cache = null;
            this.setDirtyCanvas(true);
            return true;
        };
    }
});
