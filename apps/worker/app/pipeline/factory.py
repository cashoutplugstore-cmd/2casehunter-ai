from __future__ import annotations

from typing import Any

from .experiment import build_experiment
from .feedback import feedback_signal
from .policy import review_policy
from .production import build_production_plan
from .providers import submit_render_job
from .publish import build_publish_job
from .render import build_render_job
from .script import build_short_script
from .service import build_blueprint


def run_factory(story: dict[str, Any], metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the local content factory without calling paid external providers."""
    policy = review_policy(story)
    if policy["status"] == "blocked":
        return {"status": "blocked", "policy": policy}

    blueprint = build_blueprint(story, target="arabic-short-form")
    experiment = build_experiment(blueprint["blueprint"])
    script = build_short_script(blueprint["blueprint"])
    production = build_production_plan(script)
    render_job = build_render_job(production)
    render = submit_render_job(render_job)

    video = {
        "title": production.get("title", story.get("title", "")),
        "render": render,
        "status": "render_queued",
    }
    publish = build_publish_job(video, "tiktok")
    feedback = feedback_signal(metrics or {})

    return {
        "status": "ready_for_execution",
        "policy": policy,
        "blueprint": blueprint,
        "experiment": experiment,
        "script": script,
        "production": production,
        "render": render,
        "publish": publish,
        "feedback": feedback,
    }
