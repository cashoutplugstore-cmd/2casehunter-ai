from __future__ import annotations

from typing import Any

from ..config import settings


def _fallback_script(title: str, hook: str, angle: str) -> str:
    """No-cost fallback. Never pretends to translate an English story."""
    if angle and any(ord(ch) > 127 for ch in angle):
        return "\n\n".join(
            part for part in (
                hook or f"خلينا نفهم شنو صار بـ{title}.",
                angle,
                "شنو رأيك؟ تابعنا للمزيد من القصص والتحليلات.",
            ) if part
        )

    return "\n\n".join(
        part for part in (
            hook or f"خلينا نفهم شنو صار بـ{title}.",
            "هذا الخبر يحتاج تحويلًا عربيًا بواسطة مزود AI قبل إنشاء النص النهائي.",
            "شنو رأيك؟ تابعنا للمزيد من القصص والتحليلات.",
        ) if part
    )


def _openai_script(title: str, summary: str) -> str | None:
    """Use OpenAI only when the user explicitly configured an API key."""
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model="gpt-5-mini",
            input=(
                "حوّل الخبر التالي إلى سكربت عربي قصير باللهجة العراقية الخفيفة. "
                "لا تضف معلومات غير موجودة في المصدر. اجعل النص مناسبًا لفيديو 20-30 ثانية، "
                "ابدأ بخطاف جذاب، ثم أهم معلومتين أو ثلاث، واختم بسؤال قصير. "
                "أخرج النص فقط بدون Markdown.\n\n"
                f"العنوان: {title}\n"
                f"المصدر: {summary}"
            ),
        )
        text = getattr(response, "output_text", None)
        return text.strip() if text else None
    except Exception:
        return None


def build_short_script(blueprint: dict[str, Any]) -> dict[str, Any]:
    """Turn a reviewed blueprint into an Arabic short-form script draft."""
    title = str(blueprint.get("title") or "").strip()
    hook = str(blueprint.get("hook") or "").strip()
    angle = str(blueprint.get("angle") or "").strip()

    if not title:
        raise ValueError("blueprint.title is required")

    script = _openai_script(title, angle) or _fallback_script(title, hook, angle)

    return {
        "title": title,
        "format": "short",
        "language": "ar",
        "script": script,
        "ai_provider": "openai" if settings.openai_api_key else "fallback",
        "status": "ready_for_review",
    }
