# Integrated Network Platform

This is the unified codebase consolidating `network-d3js`, `enhanced-network-api-corporate`, and `cisco-meraki-cli-enhanced`.

## Structure

*   **`api/`**: FastAPI backend. served at port 11100.
    *   `main.py`: Entry point.
    *   `endpoints/`: API logic.
*   **`shared/`**: Core shared libraries (Discovery, Viz, Auth).
*   **`exports/static/`**: Static assets (HTML, JS, CSS).
    *   `landing.html`: The main dashboard.
    *   `ui/`: The legacy D3.js app.
*   **`icons/`**: Consolidated Device Icons (SVG).
*   **`models/`**: 3D Models for the renderer.
*   **`scripts/`**: Utility scripts (CLI tools).
*   **`archive/`**: Cleanup of obsolete code/assets.
*   **`archived_projects/`**: Original source code for reference.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install meraki mac-vendor-lookup
    ```

2.  **Configure Environment**:
    Edit `.env` with your credentials:
    *   `MERAKI_API_KEY`
    *   `FORTIGATE_HOST`, `FORTIGATE_TOKEN`

3.  **Run**:
    ```bash
    uvicorn api.main:app --host 0.0.0.0 --port 11100 --reload
    ```

## Usage

*   **Dashboard**: [http://localhost:11100/](http://localhost:11100/)
*   **D3 Map**: Click "Interactive Map" on dashboard.
*   **3D Map**: Click "3D Explorer" -> "Generate".
*   **Meraki**: Enter ID and click "Go".

## Features

*   **Offline Ready**: All JS libraries (Three.js, D3) are local.
*   **Secure**: Supports SSL verifications and corporate proxy detection.
*   **Unified**: One API for all network tasks.
