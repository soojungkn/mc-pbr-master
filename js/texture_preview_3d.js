import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Load Three.js from local extension files
async function loadThreeJS() {
    if (window.THREE) {
        return window.THREE;
    }

    // Get the path to this extension's directory
    const scriptPath = import.meta.url;
    const basePath = scriptPath.substring(0, scriptPath.lastIndexOf('/'));

    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `${basePath}/three.min.js`;
        script.onload = () => {
            if (window.THREE) {
                resolve(window.THREE);
            } else {
                reject(new Error("Three.js loaded but THREE object not found"));
            }
        };
        script.onerror = () => {
            reject(new Error("Failed to load three.min.js from extension directory"));
        };
        document.head.appendChild(script);
    });
}

app.registerExtension({
    name: "MicroCreativity.TexturePreview3D",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "MC_TexturePreview3D") return;

        nodeType.prototype.onNodeCreated = function () {
            const node = this;

            // Set a sensible default node size so the 3D preview is
            // visible as soon as the node is dropped on the canvas.
            this.size = [400, 500];

            // Create canvas container
            const container = document.createElement("div");
            container.style.cssText = `
                width: 100%;
                height: 100%;
                background: #2a2a2a;
                border: 1px solid #555;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #aaa;
                font-size: 13px;
                overflow: hidden;
            `;
            container.textContent = "Loading Three.js...";

            // Add as widget
            // We use a dummy widget to hold the DOM element
            // "serialize: false" prevents it from being saved to the workflow JSON
            node.addDOMWidget("viewer3d", "div", container, {
                serialize: false,
                hideOnZoom: false
            });

            node.viewer_container = container;
            node.viewer_data = null;

            // Initialize
            loadThreeJS().then(THREE => {
                node.initScene(THREE, container);
                // Trigger initial resize after load
                if (node.onResize) node.onResize(node.size);
            }).catch(err => {
                container.innerHTML = `
                    <div style="padding: 20px; text-align: center;">
                        <div style="color: #ff6666;">Error loading Three.js</div>
                        <div style="font-size: 11px; margin-top: 10px; color: #999;">
                            Make sure three.min.js is in your extension folder
                        </div>
                    </div>
                `;
            });
        };

        // Resizing logic — sync the Three.js renderer to
        // whatever size ComfyUI has given the DOM widget container.
        nodeType.prototype.onResize = function () {
            if (!this.viewer_container || !this.viewer_data) return;
            const { renderer, camera } = this.viewer_data;
            if (!renderer || !camera) return;

            const w = this.viewer_container.clientWidth;
            const h = this.viewer_container.clientHeight;
            if (w < 1 || h < 1) return;           // not visible yet

            renderer.setSize(w, h);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
        };

        nodeType.prototype.initScene = function (THREE, container) {
            const node = this;
            container.textContent = "";

            // Create canvas
            const canvas = document.createElement('canvas');
            // Initial size, will be resized immediately by onResize
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.display = 'block';
            container.appendChild(canvas);

            // Scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x2a2a2a);

            // Camera (Aspect will be fixed in onResize)
            const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
            camera.position.z = 3;

            // Renderer
            const renderer = new THREE.WebGLRenderer({
                canvas: canvas,
                antialias: true
            });
            // Start at a minimal size; the animate() loop will immediately
            // resize it to match the container once layout is complete.
            renderer.setSize(10, 10);

            // Lights
            const ambient = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambient);

            const light1 = new THREE.DirectionalLight(0xffffff, 0.8);
            light1.position.set(5, 5, 5);
            scene.add(light1);

            const light2 = new THREE.DirectionalLight(0xffffff, 0.3);
            light2.position.set(-5, -3, -5);
            scene.add(light2);

            // Mesh
            const material = new THREE.MeshStandardMaterial({
                color: 0xaaaaaa,
                roughness: 0.7,
                metalness: 0.1
            });

            const geometry = new THREE.SphereGeometry(1, 64, 64);
            const mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);

            // Store data
            node.viewer_data = {
                THREE, scene, camera, renderer, mesh, canvas,
                rotation: { x: 0, y: 0 },
                lightAngle: Math.PI / 4,
                lightDistance: 7,
                lightHeight: 3,
                dragging: false,
                isLightOrbitMode: false,
                lastX: 0,
                lastY: 0
            };

            node.main_light = light1;

            // Events
            canvas.onmousedown = (e) => {
                node.viewer_data.dragging = true;
                node.viewer_data.lastX = e.clientX;
                node.viewer_data.lastY = e.clientY;
                node.viewer_data.isLightOrbitMode = e.shiftKey && (e.button === 0);
                canvas.style.cursor = node.viewer_data.isLightOrbitMode ? 'ew-resize' : 'grabbing';
                e.preventDefault();
                e.stopPropagation();
            };

            canvas.onmousemove = (e) => {
                if (!node.viewer_data.dragging) {
                    canvas.style.cursor = 'grab';
                    return;
                }
                const dx = e.clientX - node.viewer_data.lastX;
                const dy = e.clientY - node.viewer_data.lastY;

                if (node.viewer_data.isLightOrbitMode) {
                    node.viewer_data.lightAngle += dx * 0.01;
                    const x = Math.cos(node.viewer_data.lightAngle) * node.viewer_data.lightDistance;
                    const z = Math.sin(node.viewer_data.lightAngle) * node.viewer_data.lightDistance;
                    const y = node.viewer_data.lightHeight;
                    if (node.main_light) {
                        node.main_light.position.set(x, y, z);
                        node.main_light.lookAt(0, 0, 0);
                    }
                } else {
                    node.viewer_data.rotation.y += dx * 0.01;
                    node.viewer_data.rotation.x += dy * 0.01;
                    if (node.viewer_data.mesh) {
                        node.viewer_data.mesh.rotation.y = node.viewer_data.rotation.y;
                        node.viewer_data.mesh.rotation.x = node.viewer_data.rotation.x;
                    }
                }
                node.viewer_data.lastX = e.clientX;
                node.viewer_data.lastY = e.clientY;
                e.preventDefault();
                e.stopPropagation();
            };

            canvas.onmouseup = (e) => {
                node.viewer_data.dragging = false;
                node.viewer_data.isLightOrbitMode = false;
                canvas.style.cursor = 'grab';
            };

            canvas.onmouseleave = (e) => {
                node.viewer_data.dragging = false;
                canvas.style.cursor = 'default';
            };

            canvas.onwheel = (e) => {
                camera.position.z += e.deltaY * 0.005;
                camera.position.z = Math.max(1.5, Math.min(10, camera.position.z));
                e.preventDefault();
                e.stopPropagation();
            };

            function animate() {
                if (!node.viewer_data) return;
                requestAnimationFrame(animate);

                // Auto-sync renderer size to container
                const cw = container.clientWidth;
                const ch = container.clientHeight;
                if (cw > 0 && ch > 0) {
                    const needsResize = canvas.width !== cw || canvas.height !== ch;
                    if (needsResize) {
                        renderer.setSize(cw, ch);
                        camera.aspect = cw / ch;
                        camera.updateProjectionMatrix();
                    }
                }

                renderer.render(scene, camera);
            }
            animate();

            // Setup widget listener
            const meshTypeWidget = node.widgets.find(w => w.name === "mesh_type");
            if (meshTypeWidget) {
                const originalCallback = meshTypeWidget.callback;
                meshTypeWidget.callback = function (value) {
                    if (originalCallback) originalCallback.apply(this, arguments);
                    node.updateMesh(value);
                };
            }

            // Trigger initial resize using current node size
            if (node.onResize) node.onResize(node.size);
        };

        nodeType.prototype.updateMesh = function (meshType) {
            if (!this.viewer_data) return;
            const { THREE, scene, mesh } = this.viewer_data;
            const material = mesh.material;
            const currentRotation = {
                x: this.viewer_data.rotation.x || 0,
                y: this.viewer_data.rotation.y || 0,
                z: 0
            };

            scene.remove(mesh);
            if (mesh.geometry) mesh.geometry.dispose();

            const finalMeshType = meshType || this.widgets.find(w => w.name === "mesh_type")?.value || 'Sphere';
            let geometry;
            switch (finalMeshType) {
                case 'Sphere': geometry = new THREE.SphereGeometry(1, 64, 64); break;
                case 'Plane': geometry = new THREE.PlaneGeometry(2, 2, 128, 128); break;
                case 'Cube': geometry = new THREE.BoxGeometry(1.5, 1.5, 1.5, 32, 32, 32); break;
                default: geometry = new THREE.SphereGeometry(1, 64, 64);
            }

            const newMesh = new THREE.Mesh(geometry, material);
            newMesh.rotation.set(currentRotation.x, currentRotation.y, currentRotation.z);
            scene.add(newMesh);
            this.viewer_data.mesh = newMesh;
        };

        nodeType.prototype.onExecuted = function (message) {
            if (!this.viewer_data) return;
            const { THREE } = this.viewer_data;
            if (!this.viewer_data.mesh) this.updateMesh();

            if (!message?.texture_files) return;

            const loader = new THREE.TextureLoader();
            for (const file of message.texture_files) {
                const url = api.apiURL(
                    `/view?filename=${encodeURIComponent(file.filename)}&type=${file.type}&subfolder=${file.subfolder}`
                );

                loader.load(url, (texture) => {
                    texture.wrapS = THREE.RepeatWrapping;
                    texture.wrapT = THREE.RepeatWrapping;
                    const mat = this.viewer_data.mesh.material;

                    if (file.role === 'base_color') mat.map = texture;
                    else if (file.role === 'roughness') { mat.roughnessMap = texture; mat.roughness = 1.0; }
                    else if (file.role === 'normal') mat.normalMap = texture;
                    else if (file.role === 'metallic') { mat.metalnessMap = texture; mat.metalness = 1.0; }
                    else if (file.role === 'ao') { mat.aoMap = texture; mat.aoMapIntensity = 1.0; }
                    else if (file.role === 'displacement') {
                        mat.displacementMap = texture;
                        mat.displacementScale = 0.1;
                        mat.displacementBias = -0.05;
                    }
                    mat.needsUpdate = true;
                });
            }
        };

        nodeType.prototype.onRemoved = function () {
            if (this.viewer_data) {
                this.viewer_data.renderer.dispose();
                this.viewer_data.mesh.geometry.dispose();
                this.viewer_data.mesh.material.dispose();
                this.viewer_data = null;
            }
        };
    }
});