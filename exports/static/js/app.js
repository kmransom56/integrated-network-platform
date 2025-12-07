document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadDashboardData();

    document.getElementById('runDiscoveryBtn').addEventListener('click', runDiscovery);
});

function initNavigation() {
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            // Remove active class
            links.forEach(l => l.classList.remove('active'));
            document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));

            // Add active class
            e.currentTarget.classList.add('active');
            const targetId = e.currentTarget.dataset.target;
            document.getElementById(targetId).classList.add('active');

            // Update Title
            const titleMap = {
                'dashboard': 'Network Overview',
                'topology': 'Topology Map',
                'inventory': 'Device Inventory',
                'settings': 'Settings'
            };
            document.getElementById('pageTitle').innerText = titleMap[targetId];
        });
    });
}

async function loadDashboardData() {
    console.log("Loading dashboard data...");

    // Initialize Topology Viewer
    const viewer = new TopologyViewer('vizFrame', {
        backgroundColor: 'rgba(15, 23, 42, 0)' // Transparent to show container bg
    });
    await viewer.init();

    // 2. Load Device Stats & Topology
    try {
        const statsResp = await fetch('/api/v1/devices');
        if (statsResp.ok) {
            const data = await statsResp.json();

            // Build simple topology from device list (Hub and Spoke for now)
            const links = [];
            let coreId = null;

            if (data.devices) {
                // Find potential core
                const core = data.devices.find(d =>
                    (d.device_type || '').toLowerCase().includes('gate') ||
                    (d.device_type || '').toLowerCase().includes('firewall')
                );
                coreId = core ? core.id : (data.devices[0] ? data.devices[0].id : null);

                if (coreId) {
                    data.devices.forEach(d => {
                        if (d.id !== coreId) {
                            links.push({ source: coreId, target: d.id });
                        }
                    });
                }

                // Load data into viewer
                viewer.loadData({
                    nodes: data.devices.map(d => ({
                        id: d.id,
                        name: d.name || d.id,
                        type: normalizeType(d.device_type),
                        ...d
                    })),
                    links: links
                });
            }

            // Calculate stats
            let gateways = 0;
            let clients = 0;
            let alerts = 0;

            if (data.devices) {
                data.devices.forEach(d => {
                    const type = (d.device_type || '').toLowerCase();
                    if (type.includes('gate') || type.includes('firewall')) gateways++;
                    if (type.includes('client') || type.includes('mobile') || type.includes('host')) clients++;
                    // Simple alert logic: if status is down/offline
                    if (d.status && d.status.toLowerCase() !== 'online') alerts++;
                });

                updateStats({
                    total: data.total_count,
                    gateways: gateways,
                    clients: clients,
                    alerts: alerts,
                    devices: data.devices // Pass full list for table
                });
            }
        }
    } catch (e) {
        console.error("Failed to load stats:", e);
    }
}

function updateStats(data) {
    document.getElementById('totalDevices').innerText = data.total;
    document.getElementById('totalGateways').innerText = data.gateways;
    document.getElementById('totalClients').innerText = data.clients;
    document.getElementById('activeAlerts').innerText = data.alerts;

    // Populate Table
    const tbody = document.getElementById('deviceTableBody');
    tbody.innerHTML = '';

    // Use real data if available, or fallback to demo
    const devicesToRender = data.devices || [
        { status: 'online', name: 'FortiGate-100F', ip_address: '192.168.1.99', device_type: 'Firewall', vendor: 'Fortinet', metadata: { cpu: '12%' } },
        { status: 'online', name: 'Core-Switch', ip_address: '192.168.1.2', device_type: 'Switch', vendor: 'Cisco', metadata: { cpu: '45%' } },
    ];

    devicesToRender.slice(0, 15).forEach(d => {
        // Safe access
        let cpuVal = '-';
        if (d.metadata) {
            if (d.metadata.cpu) {
                cpuVal = typeof d.metadata.cpu === 'object' ? (d.metadata.cpu.cpu || '0') : d.metadata.cpu;
            }
        }

        // Normalize status color
        const status = (d.status || 'unknown').toLowerCase();
        const statusClass = status === 'online' ? 'status-online' : (status === 'offline' ? 'status-offline' : 'status-warning');

        // Handle CPU bar
        let cpuBar = '-';
        if (cpuVal !== '-' && cpuVal !== undefined) {
            // clean string like "12%" -> 12
            const cpuNum = parseInt(String(cpuVal).replace('%', '')) || 0;
            cpuBar = `
                <div style="width: 100px; height: 6px; background: #334155; border-radius: 3px; overflow: hidden;">
                    <div style="width: ${cpuNum}%; height: 100%; background: ${cpuNum > 80 ? '#ef4444' : '#3b82f6'};"></div>
                </div>
                <span style="font-size: 11px;">${cpuVal}%</span>
            `;
        }

        const row = `
        <tr class="table-row">
            <td><span class="status-dot ${statusClass}"></span>${status}</td>
            <td style="font-weight: 500;">${d.name || d.id || 'Unknown'}</td>
            <td style="font-family: monospace;">${d.ip_address || '-'}</td>
            <td>${d.device_type}</td>
            <td>${d.vendor}</td>
            <td>${cpuBar}</td>
        </tr>
        `;
        tbody.innerHTML += row;
    });
}

function normalizeType(type) {
    if (!type) return 'endpoint';
    const t = type.toLowerCase();
    if (t.includes('gate') || t.includes('firewall')) return 'fortigate';
    if (t.includes('switch')) return 'fortiswitch';
    if (t.includes('access point') || t.includes('ap')) return 'access_point';
    if (t.includes('server')) return 'server';
    return 'endpoint';
}

async function runDiscovery() {
    const btn = document.getElementById('runDiscoveryBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-sync fa-spin"></i> Discovery in Progress...';
    btn.disabled = true;

    try {
        // Trigger discovery API
        const response = await fetch('/api/v1/devices/collect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                // Default creds or read from a form
                host: '192.168.1.99',
                username: 'admin'
            })
        });

        if (response.ok) {
            alert("Discovery initiated successfully!");
            // Reload data after a delay to allow processing
            setTimeout(loadDashboardData, 2000);
        } else {
            alert("Failed to start discovery.");
        }
    } catch (e) {
        console.error(e);
        alert("Error during discovery.");
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
