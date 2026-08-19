from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl

from .db import get_supabase
from .pipeline.production import build_production_plan
from .pipeline.runner import run_feed_pipeline
from .pipeline.script import build_short_script
from .pipeline.service import build_blueprint
from .radar.service import scan_feed

app = FastAPI(title="CaseHunter AI Worker", version="0.7.0")


class RadarScanRequest(BaseModel):
    feed_url: HttpUrl
    source_name: str = "RSS"


class PipelineRunRequest(BaseModel):
    feed_url: HttpUrl
    source_name: str = "RSS"
    target: str = "arabic-short-form"


class BlueprintRequest(BaseModel):
    title: str
    summary: str = ""
    source_url: HttpUrl | None = None
    score: float | None = None
    target: str = "arabic-short-form"


class ScriptRequest(BaseModel):
    blueprint: dict


class ProductionRequest(BaseModel):
    script: dict


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CaseHunter AI</title>
<style>body{margin:0;background:#0b1020;color:#eef2ff;font-family:system-ui,-apple-system,sans-serif}main{max-width:1000px;margin:auto;padding:40px 20px}header{margin-bottom:28px}h1{font-size:36px;margin:0 0 8px}p{color:#aab4d0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.card{background:#151c31;border:1px solid #29324d;border-radius:16px;padding:22px}.card b{display:block;font-size:18px;margin-bottom:8px}.status{color:#66e3a4}code{background:#0f1528;padding:3px 7px;border-radius:6px}</style></head>
<body><main><header><h1>CaseHunter AI</h1><p>منصة اكتشاف وتحليل وتجهيز المحتوى بالذكاء الاصطناعي</p></header>
<div class="grid"><div class="card"><b>🔎 اكتشاف</b><span>Radar للأخبار والمصادر</span></div><div class="card"><b>📊 تحليل</b><span>تقييم القصص والمصادر</span></div><div class="card"><b>🎯 استهداف</b><span>تحديد الجمهور والصيغة</span></div><div class="card"><b>📝 تجهيز</b><span>Content Blueprint</span></div><div class="card"><b>✍️ سكربت</b><span>مسودة Short أصلية</span></div><div class="card"><b>🎬 إنتاج</b><span>خطة مشاهد وصوت وترجمة</span></div><div class="card"><b>🚀 نشر</b><span>جاهز لربط منصات النشر</span></div><div class="card"><b>📈 Analytics</b><span>جاهز لتتبع النتائج</span></div><div class="card"><b>● API</b><span class="status">Online</span></div></div>
<p style="margin-top:28px">Health: <code>/health</code> · Radar: <code>/radar/scan</code> · Pipeline: <code>/pipeline/run</code> · Script: <code>/pipeline/script</code> · Production: <code>/pipeline/production</code></p>
</main></body></html>"""


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


@app.post("/pipeline/run")
def pipeline_run(request: PipelineRunRequest) -> dict:
    try:
        return run_feed_pipeline(str(request.feed_url), source_name=request.source_name, target=request.target)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Pipeline could not process the RSS feed") from exc


@app.post("/pipeline/blueprint")
def pipeline_blueprint(request: BlueprintRequest) -> dict:
    try:
        return build_blueprint(request.model_dump(), target=request.target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/pipeline/script")
def pipeline_script(request: ScriptRequest) -> dict:
    try:
        return build_short_script(request.blueprint)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/pipeline/production")
def pipeline_production(request: ProductionRequest) -> dict:
    try:
        return build_production_plan(request.script)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/radar/scan-sources")
def radar_scan_sources() -> dict:
    try:
        supabase = get_supabase()
        response = supabase.table("sources").select("id,name,url,country,language").eq("active", True).execute()
        sources = response.data or []
        saved = 0
        scanned = 0
        failed: list[dict[str, str]] = []
        for source in sources:
            try:
                items = scan_feed(source["url"], source["name"])
                scanned += len(items)
                rows = [{"title": item["title"], "summary": item["summary"], "country": source.get("country"), "category": "news", "source_count": 1, "score": item["score"], "status": "discovered", "source_url": item["url"]} for item in items]
                if rows:
                    result = supabase.table("stories").upsert(rows, on_conflict="source_url", ignore_duplicates=True).execute()
                    saved += len(result.data or [])
            except Exception as exc:
                failed.append({"source": source["name"], "error": str(exc)})
        return {"sources": len(sources), "scanned": scanned, "saved": saved, "failed": failed}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Radar database scan failed") from exc
