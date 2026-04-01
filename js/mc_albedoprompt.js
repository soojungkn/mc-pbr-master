import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "MC.AlbedoPromptEngine",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MC_AlbedoPrompt") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                // Set wider node width
                this.size[0] = 350;

                return r;
            };
        }
    },
});
