from __future__ import annotations

import re
from typing import Any

import httpx

from ..config import settings


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


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


def _mymemory_translate(text: str) -> str | None:
    """Free public translation fallback; no API key required."""
    text = _clean_text(text)
    if not text:
        return None

    try:
        response = httpx.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:4500], "langpair": "en|ar"},
            timeout=12.0,
            follow_redirects=True,
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get("responseData", {}).get("translatedText")
        if translated and isinstance(translated, str):
            translated = _clean_text(translated)
            if translated and translated.lower() != text.lower():
                return translated
    except Exception:
        pass
    return None


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
    title = _clean_text(str(blueprint.get("title") or "").strip())
    hook = _clean_text(str(blueprint.get("hook") or "").strip())
    angle = _clean_text(str(blueprint.get("angle") or "").strip())

    if not title:
        raise ValueError("blueprint.title is required")

    ai_script = _openai_script(title, angle)
    translated = None
    if not ai_script:
        translated = _mymemory_translate(angle)

    if ai_script:
        script = ai_script
        provider = "openai"
    elif translated:
        script = "\n\n".join(
            part for part in (
                hook or f"خلينا نفهم شنو صار بـ{title}.",
                translated,
                "شنو رأيك؟ تابعنا للمزيد من القصص والتحليلات.",
            ) if part
        )
        provider = "mymemory-free"
    else:
        script = _fallback_script(title, hook, angle)
        provider = "fallback"

    return {
        "title": title,
        "format": "short",
        "language": "ar",
        "script": script,
        "ai_provider": provider,
        "status": "ready_for_review",
    }
