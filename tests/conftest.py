import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# You can add global fixtures here
import pytest

@pytest.fixture(scope="session")
def project_root():
    return root_dir
