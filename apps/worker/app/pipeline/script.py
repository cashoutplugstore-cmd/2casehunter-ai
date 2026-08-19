from __future__ import annotations

import re
from typing import Any

import httpx

from ..config import settings


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _shorten(text: str, limit: int = 520) -> str:
    """Keep a useful short-form chunk and prefer a sentence boundary."""
    text = _clean_text(text)
    if len(text) <= limit:
        return text
    chunk = text[:limit]
    boundaries = [chunk.rfind("."), chunk.rfind("؟"), chunk.rfind("!"), chunk.rfind(".")]
    boundary = max(boundaries)
    if boundary >= int(limit * 0.55):
        return chunk[: boundary + 1].strip()
    return chunk.rsplit(" ", 1)[0].strip() + "…"


def _split_for_translation(text: str, max_chars: int = 300) -> list[str]:
    """Split source text into conservative MyMemory-sized chunks."""
    text = _clean_text(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            words = sentence.split()
            piece = ""
            for word in words:
                candidate = f"{piece} {word}".strip()
                if len(candidate) > max_chars and piece:
                    chunks.append(piece)
                    piece = word
                else:
                    piece = candidate
            if piece:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.append(piece)
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _fallback_script(title: str, hook: str, angle: str) -> str:
    """No-cost fallback. Never pretends to translate an English story."""
    if angle and any(ord(ch) > 127 for ch in angle):
        return "\n\n".join(
            part for part in (
                hook or f"خلينا نفهم شنو صار بـ{title}.",
                _shorten(angle),
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


def _translate_chunk(client: httpx.Client, text: str) -> str | None:
    try:
        response = client.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "en|ar"},
            timeout=12.0,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("responseStatus") not in (None, 200):
            return None
        translated = data.get("responseData", {}).get("translatedText")
        if not translated or not isinstance(translated, str):
            return None
        translated = _clean_text(translated)
        lowered = translated.lower()
        if not translated or lowered == text.lower():
            return None
        if "query length limit exceeded" in lowered or "max allowed query" in lowered:
            return None
        return translated
    except Exception:
        return None


def _mymemory_translate(text: str, limit: int = 300) -> str | None:
    """Free public translation fallback using conservative request sizes."""
    chunks = _split_for_translation(_clean_text(text), max_chars=min(limit, 300))
    if not chunks:
        return None

    translated_chunks: list[str] = []
    try:
        with httpx.Client(follow_redirects=True) as client:
            for chunk in chunks:
                translated = _translate_chunk(client, chunk)
                if not translated:
                    return None
                translated_chunks.append(translated)
    except Exception:
        return None

    result = _clean_text(" ".join(translated_chunks))
    return result or None


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
    translated_title = None
    if not ai_script:
        translated = _mymemory_translate(angle)
        if title and not any(ord(ch) > 127 for ch in title):
            translated_title = _mymemory_translate(title)

    if ai_script:
        script = ai_script
        output_title = title
        provider = "openai"
    elif translated:
        output_title = translated_title or title
        output_hook = f"شنو القصة؟ {output_title}"
        script = "\n\n".join(
            part for part in (
                output_hook,
                _shorten(translated),
                "شنو رأيك؟ تابعنا للمزيد من القصص والتحليلات.",
            ) if part
        )
        provider = "mymemory-free"
    else:
        output_title = title
        script = _fallback_script(output_title, hook, angle)
        provider = "fallback"

    return {
        "title": output_title,
        "format": "short",
        "language": "ar",
        "script": script,
        "ai_provider": provider,
        "status": "ready_for_review",
    }
