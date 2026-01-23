import pytest
import redis.asyncio as redis
from unittest.mock import AsyncMock
from src.cache.redis_manager import CacheManager


@pytest.fixture
def mock_redis():
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    return mock_client


@pytest.mark.asyncio
async def test_cache_operations(mock_redis):
    """Test basic cache operations."""
    cache = CacheManager()
    cache.client = mock_redis
    
    # Test get/set
    test_key = "test-key"
    test_value = {"score": 85}
    
    await cache.set(test_key, test_value)
    mock_redis.setex.assert_called_once()
    
    result = await cache.get(test_key)
    assert result == test_value
    
    # Test delete
    await cache.delete(test_key)
    mock_redis.delete.assert_called_once()
