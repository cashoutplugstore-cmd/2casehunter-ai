from __future__ import annotations

from typing import Any

from .experiment import build_experiment
from .feedback import feedback_signal
from .policy import review_policy
from .production import build_production_plan
from .providers import submit_render_job
from .publish import build_publish_job
from .render import build_render_job
from .runner import run_feed_pipeline
from .script import build_short_script


def run_content_factory(
    feed_url: str,
    source_name: str = "RSS",
    target: str = "arabic-short-form",
    platform: str = "tiktok",
) -> dict[str, Any]:
    """Run the complete local content workflow without paid provider calls."""
    pipeline = run_feed_pipeline(feed_url, source_name=source_name, target=target, persist=False)
    if pipeline.get("status") != "ready_for_review":
        return {"status": pipeline.get("status", "no_story"), "stage": "discovery", "pipeline": pipeline}

    story = pipeline["story"]
    policy = review_policy(story)
    if policy["status"] != "approved_for_generation":
        return {"status": "blocked", "stage": "safety", "pipeline": pipeline, "policy": policy}

    blueprint = pipeline["blueprint"]
    experiment = build_experiment(blueprint)
    script = build_short_script(blueprint)
    production = build_production_plan(script)
    render_job = build_render_job(production)
    render_submission = submit_render_job(render_job)
    publish_job = build_publish_job(
        {"title": production.get("title", blueprint.get("title", "")), "render": render_submission},
        platform=platform,
    )

    return {
        "status": "ready_for_publish",
        "stage": "publish_queue",
        "story": story,
        "policy": policy,
        "experiment": experiment,
        "blueprint": blueprint,
        "script": script,
        "production": production,
        "render": render_job,
        "render_submission": render_submission,
        "publish": publish_job,
        "feedback": feedback_signal({}),
    }
