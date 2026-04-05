import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Shorten a path like "C:\Users\Foo\Very\Long\Path\To\Folder"
// into "C:\Users\...\To\Folder" to fit within maxLen characters.
function shortenPath(fullPath, maxLen = 35) {
    if (!fullPath || fullPath.length <= maxLen) return fullPath;

    const sep = fullPath.includes("\\") ? "\\" : "/";
    const parts = fullPath.split(sep);

    if (parts.length <= 3) return fullPath;

    // Keep first part (drive/root) and last 2 parts
    const head = parts[0];
    const tail = parts.slice(-2).join(sep);
    const shortened = head + sep + "..." + sep + tail;

    // If still too long, just keep drive + last folder
    if (shortened.length > maxLen) {
        return head + sep + "..." + sep + parts[parts.length - 1];
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

            // Leave the save_path widget visible so users can always see
            // the current path. The browse button writes into it.
            const node = this;
            const initialLabel = "Browse...";

            const browseBtn = this.addWidget(
                "button",
                "browse_folder",
                initialLabel,
                () => {
                    // Non-async wrapper so LiteGraph doesn't choke on a
                    // Promise return value from the callback.
                    api.fetchApi("/mc/pick_folder", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            initial_dir: pathWidget.value || ""
                        })
                    })
                        .then(resp => resp.json())
                        .then(data => {
                            if (data.path) {
                                pathWidget.value = data.path;
                                node.setDirtyCanvas(true);
                            }
                        })
                        .catch(err => {
                            console.error("[MC PBR] Folder picker error:", err);
                        });
                }
            );
            browseBtn.serialize = false;
        };
    }
});
