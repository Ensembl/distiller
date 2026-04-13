import pytest
from backend.core.config import get_config, ConfigError

def test_config_load():
    config = get_config()
    
    assert config
    
def test_bad_config_load():

    with pytest.raises(ConfigError):
        config = get_config("bad.path")
