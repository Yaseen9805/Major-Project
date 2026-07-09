from cache import SemanticCache


def test_hit_for_near_duplicate_paraphrase():
    cache = SemanticCache(threshold=0.8)
    cache.add("What is the capital of France?", "Paris", "small")

    result = cache.check("Can you tell me France's capital city?")

    assert result is not None
    assert result["answer"] == "Paris"


def test_miss_for_unrelated_query():
    cache = SemanticCache(threshold=0.87)
    cache.add("What is the capital of France?", "Paris", "small")

    result = cache.check("What is the airspeed velocity of an unladen swallow?")

    assert result is None


def test_miss_on_empty_cache():
    cache = SemanticCache()
    assert cache.check("Anything at all?") is None


def test_add_increases_cache_size():
    cache = SemanticCache()
    assert len(cache) == 0
    cache.add("What is 2+2?", "4", "small")
    assert len(cache) == 1
