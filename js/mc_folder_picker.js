import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Shorten a path like "C:\Users\Foo\Very\Long\Path\To\Folder"
// into "C:\Users\…\To\Folder" to fit within maxLen characters.
function shortenPath(fullPath, maxLen = 30) {
    if (!fullPath || fullPath.length <= maxLen) return fullPath;

    const sep = fullPath.includes("\\") ? "\\" : "/";
    const parts = fullPath.split(sep);

    if (parts.length <= 3) return fullPath;

    // Keep first part (drive/root) and last 2 parts
    const head = parts[0];
    const tail = parts.slice(-2).join(sep);
    const shortened = head + sep + "…" + sep + tail;

    // If still too long, just keep drive + last folder
    if (shortened.length > maxLen) {
        return head + sep + "…" + sep + parts[parts.length - 1];
    }
    return shortened;
}

app.registerExtension({
    name: "MC.PBR.FolderPicker",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "MC_PBRTextureExport") return;

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);

            const pathWidget = this.widgets?.find(w => w.name === "save_path");
            if (!pathWidget) return;

            // Hide the original string widget
            pathWidget.type = "hidden";
            pathWidget.computeSize = () => [0, -4];

            // Add a button that shows the shortened path and opens the picker
            const node = this;
            const label = pathWidget.value
                ? "📁 " + shortenPath(pathWidget.value)
                : "📁 Select Save Folder…";

            const browseBtn = this.addWidget(
                "button",
                "browse_folder",
                label,
                async () => {
                    try {
                        const resp = await api.fetchApi("/mc/pick_folder", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                initial_dir: pathWidget.value || ""
                            })
                        });
                        const data = await resp.json();
                        if (data.path) {
                            pathWidget.value = data.path;
                            browseBtn.name = "📁 " + shortenPath(data.path);
                            node.setDirtyCanvas(true);
                        }
                    } catch (err) {
                        console.error("[MC PBR] Folder picker error:", err);
                    }
                }
            );
            browseBtn.serialize = false;
        };
    }
});
