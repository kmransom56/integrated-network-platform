import pytest
from unittest.mock import patch
from shared.services.brand_detection_service import BrandDetectionService, RestaurantBrand

@pytest.fixture
def mock_deps():
    with patch("shared.services.brand_detection_service.get_organization_service"), \
         patch("shared.services.brand_detection_service.get_meraki_service"), \
         patch("shared.services.brand_detection_service.get_fortigate_inventory_service"):
         yield

def test_detect_brand_from_ip(mock_deps):
    """Test IP based detection"""
    svc = BrandDetectionService()
    
    # Sonic IP (10.0.0.0/8)
    brand, conf = svc.detect_brand_from_ip("10.5.5.5")
    assert brand == RestaurantBrand.SONIC
    assert conf == 0.8
    
    # BWW IP (10.1.0.0/16)
    brand, conf = svc.detect_brand_from_ip("10.1.5.5")
    assert brand == RestaurantBrand.BWW
    
    # Unknown
    brand, conf = svc.detect_brand_from_ip("192.168.99.99") # In sonic range (192.168.0.0/16)
    assert brand == RestaurantBrand.SONIC
    
    # Real unknown
    brand, conf = svc.detect_brand_from_ip("8.8.8.8")
    assert brand is None

