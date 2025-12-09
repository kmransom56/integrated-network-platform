// Auto-generated Babylon.js 3D Icon Loader
// Generated from VSS to SVG conversion

class Icon3DLoader {
    constructor(scene) {
        this.scene = scene;
        this.models = new Map();
        this.loadManifest();
    }
    
    async loadManifest() {
        try {
            const response = await fetch('manifest.json');
            const manifest = await response.json();
            
            for (const modelInfo of manifest.models) {
                await this.loadModel(modelInfo);
            }
        } catch (error) {
            console.error('Failed to load manifest:', error);
        }
    }
    
    async loadModel(modelInfo) {
        try {
            // For now, create a simple box mesh for each icon
            // In a real implementation, you'd load the actual 3D model
            const mesh = BABYLON.MeshBuilder.CreateBox(modelInfo.name, 
                {width: 1, height: 1, depth: 0.1}, this.scene);
            
            // Add metadata
            mesh.metadata = {
                name: modelInfo.name,
                category: modelInfo.category,
                tags: modelInfo.tags,
                svgPath: modelInfo.svgPath
            };
            
            // Create a simple material
            const material = new BABYLON.StandardMaterial(`${modelInfo.name}_mat`, this.scene);
            material.diffuseColor = new BABYLON.Color3(0.2, 0.4, 0.8);
            mesh.material = material;
            
            this.models.set(modelInfo.name, mesh);
            console.log(`Loaded model: ${modelInfo.name}`);
        } catch (error) {
            console.error(`Failed to load model ${modelInfo.name}:`, error);
        }
    }
    
    getModel(name) {
        return this.models.get(name);
    }
    
    getModelsByCategory(category) {
        const results = [];
        for (const [name, mesh] of this.models) {
            if (mesh.metadata.category === category) {
                results.push(mesh);
            }
        }
        return results;
    }
    
    getModelsByTag(tag) {
        const results = [];
        for (const [name, mesh] of this.models) {
            if (mesh.metadata.tags && mesh.metadata.tags.includes(tag)) {
                results.push(mesh);
            }
        }
        return results;
    }
}

// Usage in your Babylon.js application:
// const iconLoader = new Icon3DLoader(scene);
// const fortigate = iconLoader.getModel('FortiGate_60F');
// if (fortigate) {
//     fortigate.position = new BABYLON.Vector3(0, 1, 0);
// }
