from app.pipeline.factory import run_factory


def test_factory_queue_only():
    result = run_factory({
        "title": "Test story",
        "summary": "A safe test story for the local pipeline.",
        "source_url": "https://example.com/story",
        "category": "news",
        "risk_score": 0.0,
        "score": 80,
    })
    assert result["status"] == "ready_for_execution"
    assert result["policy"]["status"] == "approved_for_generation"
    assert result["render"]["status"] == "queued"
    assert result["publish"]["status"] == "ready_for_publish"
