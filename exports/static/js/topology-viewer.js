// topology-viewer.js
// Encapsulates 3D Force Graph logic from the Enterprise Dashboard

class TopologyViewer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.graph = null;
        this.options = {
            width: this.container.offsetWidth,
            height: this.container.offsetHeight,
            backgroundColor: '#0f172a', // Dark theme match
            ...options
        };

        this.TYPE_COLORS = {
            fortigate: '#3b82f6', // Brand Primary
            fortiswitch: '#10b981', // Success
            access_point: '#8b5cf6', // Brand Accent
            endpoint: '#64748b',   // Tertiary
            server: '#ef4444',     // Danger
            internet: '#06b6d4',   // Secondary
            switch: '#10b981',
            router: '#f59e0b'
        };
    }

    async init() {
        if (typeof ForceGraph3D === 'undefined') {
            console.error("ForceGraph3D library not loaded. Ensure 3d-force-graph.min.js is included.");
            return;
        }

        this.graph = ForceGraph3D()(this.container)
            .width(this.options.width)
            .height(this.options.height)
            .backgroundColor(this.options.backgroundColor)
            .showNavInfo(false)
            .nodeLabel('name')
            .nodeColor(node => this.TYPE_COLORS[node.type] || this.TYPE_COLORS.endpoint)
            .nodeRelSize(node => (node.type === 'fortigate' ? 8 : 4))
            .linkOpacity(0.3)
            .linkWidth(1)
            .linkColor(() => '#334155');

        // Resize handler
        window.addEventListener('resize', () => {
            this.graph.width(this.container.offsetWidth);
            this.graph.height(this.container.offsetHeight);
        });

        // Setup 3D Objects rendering (Sprites and Icons)
        this.setupNodeObjects();
    }

    setupNodeObjects() {
        this.graph.nodeThreeObject(node => {
            const group = new THREE.Group();

            // 1. Label Sprite (Canvas based)
            const sprite = this.makeLabelSprite(node.name || node.id, 24);
            sprite.position.y = -10;
            group.add(sprite);

            // 2. Icon (Geometric Fallback for now, can enhance with textures)
            let geometry, material;
            const color = this.TYPE_COLORS[node.type] || '#94a3b8';

            switch (node.type) {
                case 'fortigate':
                case 'firewall':
                    geometry = new THREE.BoxGeometry(8, 4, 8);
                    break;
                case 'switch':
                case 'fortiswitch':
                    geometry = new THREE.BoxGeometry(8, 2, 4);
                    break;
                case 'access_point':
                case 'ap':
                    geometry = new THREE.CylinderGeometry(3, 3, 1, 16);
                    break;
                default:
                    geometry = new THREE.SphereGeometry(3);
            }

            // Fallback material
            material = new THREE.MeshLambertMaterial({
                color: color,
                transparent: true,
                opacity: 0.9
            });

            const mesh = new THREE.Mesh(geometry, material);
            group.add(mesh);

            return group;
        });
    }

    makeLabelSprite(text, fontSizePx) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const pad = 12;
        ctx.font = `bold ${fontSizePx}px Inter, sans-serif`;
        const textWidth = ctx.measureText(text).width;
        canvas.width = textWidth + pad * 2;
        canvas.height = fontSizePx + pad * 2;

        // Need to reset font after resize
        ctx.font = `bold ${fontSizePx}px Inter, sans-serif`;

        // Background - Use roundRect if available, or simple rect
        ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
        if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(0, 0, canvas.width, canvas.height, 8);
            ctx.fill();
        } else {
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        // Text
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, canvas.width / 2, canvas.height / 2);

        const texture = new THREE.CanvasTexture(canvas);
        texture.minFilter = THREE.LinearFilter;

        const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
        const sprite = new THREE.Sprite(material);

        // Scale
        const scale = 0.5;
        sprite.scale.set(canvas.width * scale * 0.1, canvas.height * scale * 0.1, 1);

        return sprite;
    }

    loadData(graphData) {
        // Expected format: { nodes: [], links: [] }
        // Adapt if necessary
        const nodes = graphData.nodes || graphData.devices || [];
        const links = graphData.links || graphData.connections || [];

        // Normalize Links (source/target vs from/to)
        const normalizedLinks = links.map(l => ({
            source: l.source || l.from,
            target: l.target || l.to
        }));

        this.graph.graphData({
            nodes: nodes,
            links: normalizedLinks
        });

        // Fit to view
        setTimeout(() => {
            this.graph.zoomToFit(1000, 100);
        }, 500);
    }
}
