import pytest

from katas.lru_cache import LRUCache

pytestmark = pytest.mark.kata


def test_evicts_the_least_recently_used_key():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1  # "a" is now the most recent
    cache.put("c", 3)  # evicts "b"
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_put_updates_and_refreshes_a_key():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    cache.put("c", 3)  # evicts "b", not "a"
    assert cache.get("a") == 10
    assert cache.get("b") is None


def test_capacity_of_one():
    cache = LRUCache(1)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") is None
    assert cache.get("b") == 2
