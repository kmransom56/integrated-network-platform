"""
Meraki Visualization Endpoint
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from shared.network_utils.authentication import AuthManager
from shared.visualization.meraki_visualizer import MerakiVisualizer
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/visualize/{network_id}", response_class=HTMLResponse)
async def visualize_network(network_id: str, api_key: str = None):
    """
    Generate and serve an interactive topology map for a Meraki network.
    """
    auth = AuthManager()
    
    # Authenticate if key provided
    if api_key:
        auth.authenticate_meraki(api_key)
    
    try:
        # Retrieve initialized dashboard (will load from env/config/credentials)
        dashboard = auth.get_meraki_dashboard()
    except Exception as e:
        logger.error(f"Dashboard auth failed: {e}")
        raise HTTPException(status_code=400, detail=f"Meraki API Error: {str(e)}. Ensure MERAKI_API_KEY is set.")
        
    viz = MerakiVisualizer(dashboard)
    
    # Attempt to get network name
    net_name = f"Network {network_id}"
    try:
        # network = dashboard.networks.getNetwork(network_id)
        # net_name = network.get('name', net_name)
        # We skip this extra call for speed, but could add it.
        pass
    except:
        pass

    try:
        html_content = viz.create_visualization(network_id, net_name)
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    if not html_content:
        raise HTTPException(status_code=404, detail="Visualization produced no content (check logs)")
    
    return html_content
