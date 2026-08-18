from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from .db import get_supabase
from .pipeline.service import build_blueprint
from .radar.service import scan_feed

app = FastAPI(title="CaseHunter AI Worker", version="0.4.0")


class RadarScanRequest(BaseModel):
    feed_url: HttpUrl
    source_name: str = "RSS"


class BlueprintRequest(BaseModel):
    title: str
    summary: str = ""
    source_url: HttpUrl | None = None
    score: float | None = None
    target: str = "arabic-short-form"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "worker"}


@app.post("/radar/scan")
def radar_scan(request: RadarScanRequest) -> dict:
    try:
        items = scan_feed(str(request.feed_url), request.source_name)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="RSS feed could not be read") from exc

    return {"count": len(items), "items": items}


@app.post("/pipeline/blueprint")
def pipeline_blueprint(request: BlueprintRequest) -> dict:
    try:
        return build_blueprint(request.model_dump(), target=request.target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/radar/scan-sources")
def radar_scan_sources() -> dict:
    try:
        supabase = get_supabase()
        response = (
            supabase.table("sources")
            .select("id,name,url,country,language")
            .eq("active", True)
            .execute()
        )

        sources = response.data or []
        saved = 0
        scanned = 0
        failed: list[dict[str, str]] = []

        for source in sources:
            try:
                items = scan_feed(source["url"], source["name"])
                scanned += len(items)

                rows = [
                    {
                        "title": item["title"],
                        "summary": item["summary"],
                        "country": source.get("country"),
                        "category": "news",
                        "source_count": 1,
                        "score": item["score"],
                        "status": "discovered",
                        "source_url": item["url"],
                    }
                    for item in items
                ]

                if rows:
                    result = (
                        supabase.table("stories")
                        .upsert(rows, on_conflict="source_url", ignore_duplicates=True)
                        .execute()
                    )
                    saved += len(result.data or [])
            except Exception as exc:
                failed.append({"source": source["name"], "error": str(exc)})

        return {
            "sources": len(sources),
            "scanned": scanned,
            "saved": saved,
            "failed": failed,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Radar database scan failed") from exc
