from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl

from .db import get_supabase
from .pipeline.production import build_production_plan
from .pipeline.publish import build_publish_job
from .pipeline.providers import submit_render_job
from .pipeline.render import build_render_job
from .pipeline.runner import run_feed_pipeline
from .pipeline.script import build_short_script
from .pipeline.service import build_blueprint
from .pipeline.orchestrator import run_content_factory
from .pipeline.local_factory import run_local_factory
from .radar.service import scan_feed

app = FastAPI(title="CaseHunter AI Worker", version="1.1.0")

class RadarScanRequest(BaseModel):
    feed_url: HttpUrl
    source_name: str = "RSS"

class PipelineRunRequest(BaseModel):
    feed_url: HttpUrl
    source_name: str = "RSS"
    target: str = "arabic-short-form"

class FactoryRequest(BaseModel):
    feed_url: HttpUrl
    source_name: str = "RSS"
    target: str = "arabic-short-form"
    platform: str = "tiktok"

class LocalFactoryRequest(BaseModel):
    title: str
    summary: str = ""
    source_url: HttpUrl | None = None
    category: str = "news"
    risk_score: float = 0.0
    score: float = 80.0
    metrics: dict = {}

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

class RenderRequest(BaseModel):
    plan: dict

class SubmitRenderRequest(BaseModel):
    render_job: dict

class PublishRequest(BaseModel):
    video: dict
    platform: str = "tiktok"

@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CaseHunter AI</title><style>body{margin:0;background:#0b1020;color:#eef2ff;font-family:system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:40px 20px}h1{font-size:36px}p{color:#aab4d0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}.card{background:#151c31;border:1px solid #29324d;border-radius:16px;padding:22px}.card b{display:block;font-size:18px;margin-bottom:8px}.status{color:#66e3a4}code{background:#0f1528;padding:3px 7px;border-radius:6px}</style></head><body><main><h1>CaseHunter AI</h1><p>منصة اكتشاف وتحليل وتجهيز ونشر المحتوى بالذكاء الاصطناعي</p><div class="grid"><div class="card"><b>🔎 اكتشاف</b><span>Radar للأخبار والمصادر</span></div><div class="card"><b>🛡️ Safety</b><span>فحص قبل التوليد</span></div><div class="card"><b>📊 تحليل</b><span>تقييم القصص والمصادر</span></div><div class="card"><b>🎯 استهداف</b><span>تحديد الجمهور والصيغة</span></div><div class="card"><b>📝 تجهيز</b><span>Content Blueprint</span></div><div class="card"><b>✍️ سكربت</b><span>مسودة Short أصلية</span></div><div class="card"><b>🎬 إنتاج</b><span>خطة مشاهد وصوت وترجمة</span></div><div class="card"><b>🧩 Render</b><span>Render job + provider adapter</span></div><div class="card"><b>🚀 نشر</b><span>Publish queue جاهز</span></div><div class="card"><b>📈 Analytics</b><span>تتبع وتحسين النتائج</span></div><div class="card"><b>🧪 Experiments</b><span>اختبار Hooks وAngles</span></div><div class="card"><b>● API</b><span class="status">Online</span></div></div><p>Health: <code>/health</code> · Factory: <code>/factory/run</code> · Local test: <code>/factory/local</code></p></main></body></html>"""

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "worker"}

@app.post("/radar/scan")
def radar_scan(request: RadarScanRequest) -> dict:
    try: items = scan_feed(str(request.feed_url), request.source_name)
    except Exception as exc: raise HTTPException(status_code=502, detail="RSS feed could not be read") from exc
    return {"count": len(items), "items": items}

@app.post("/pipeline/run")
def pipeline_run(request: PipelineRunRequest) -> dict:
    try: return run_feed_pipeline(str(request.feed_url), source_name=request.source_name, target=request.target)
    except Exception as exc: raise HTTPException(status_code=502, detail="Pipeline could not process the RSS feed") from exc

@app.post("/factory/run")
def factory_run(request: FactoryRequest) -> dict:
    try: return run_content_factory(str(request.feed_url), source_name=request.source_name, target=request.target, platform=request.platform)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=502, detail="Content factory could not complete the workflow") from exc

@app.post("/factory/local")
def factory_local(request: LocalFactoryRequest) -> dict:
    try: return run_local_factory(request.model_dump(), metrics=request.metrics)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=502, detail="Local content factory could not complete the workflow") from exc

@app.post("/pipeline/blueprint")
def pipeline_blueprint(request: BlueprintRequest) -> dict:
    try: return build_blueprint(request.model_dump(), target=request.target)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/pipeline/script")
def pipeline_script(request: ScriptRequest) -> dict:
    try: return build_short_script(request.blueprint)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/pipeline/production")
def pipeline_production(request: ProductionRequest) -> dict:
    try: return build_production_plan(request.script)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/pipeline/render")
def pipeline_render(request: RenderRequest) -> dict:
    try: return build_render_job(request.plan)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/pipeline/render/submit")
def pipeline_render_submit(request: SubmitRenderRequest) -> dict:
    try: return submit_render_job(request.render_job)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/pipeline/publish")
def pipeline_publish(request: PublishRequest) -> dict:
    try: return build_publish_job(request.video, request.platform)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/radar/scan-sources")
def radar_scan_sources() -> dict:
    try:
        supabase = get_supabase()
        response = supabase.table("sources").select("id,name,url,country,language").eq("active", True).execute()
        sources = response.data or []
        saved = scanned = 0
        failed: list[dict[str, str]] = []
        for source in sources:
            try:
                items = scan_feed(source["url"], source["name"]); scanned += len(items)
                rows = [{"title": item["title"], "summary": item["summary"], "country": source.get("country"), "category": "news", "source_count": 1, "score": item["score"], "status": "discovered", "source_url": item["url"]} for item in items]
                if rows:
                    result = supabase.table("stories").upsert(rows, on_conflict="source_url", ignore_duplicates=True).execute(); saved += len(result.data or [])
            except Exception as exc: failed.append({"source": source["name"], "error": str(exc)})
        return {"sources": len(sources), "scanned": scanned, "saved": saved, "failed": failed}
    except RuntimeError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=502, detail="Radar database scan failed") from exc
