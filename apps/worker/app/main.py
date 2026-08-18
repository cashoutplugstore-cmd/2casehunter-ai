from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from .radar.service import scan_feed

app = FastAPI(title="CaseHunter AI Worker", version="0.2.0")


class RadarScanRequest(BaseModel):
    feed_url: HttpUrl
    source_name: str = "RSS"


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
