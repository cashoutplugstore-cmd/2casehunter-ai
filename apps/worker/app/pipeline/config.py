from __future__ import annotations

import os


PROVIDERS = {
    "video": "queue-only",
    "publish": "manual-review",
}


def provider_status() -> dict[str, object]:
    return {
        "video": {"provider": os.getenv("VIDEO_PROVIDER", PROVIDERS["video"]), "api_key_configured": bool(os.getenv("VIDEO_API_KEY"))},
        "publish": {"provider": os.getenv("PUBLISH_PROVIDER", PROVIDERS["publish"]), "api_key_configured": bool(os.getenv("PUBLISH_API_KEY"))},
    }
