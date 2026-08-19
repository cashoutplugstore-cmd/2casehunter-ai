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


def run_local_factory(story: dict[str, Any], metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the complete content workflow from a supplied story, without RSS or paid APIs."""
    policy = review_policy(story)
    if policy["status"] != "approved_for_generation":
        return {"status": "blocked", "stage": "safety", "policy": policy}

    blueprint_result = build_blueprint(story, target="arabic-short-form")
    blueprint = blueprint_result.get("blueprint", blueprint_result)
    experiment = build_experiment(blueprint)
    script = build_short_script(blueprint)
    production = build_production_plan(script)
    render_job = build_render_job(production)
    render_submission = submit_render_job(render_job)
    publish_job = build_publish_job(
        {"title": production.get("title", blueprint.get("title", "")), "render": render_submission},
        platform="tiktok",
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
        "feedback": feedback_signal(metrics or {}),
    }
