from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


class FFmpegProvider:
    """Render a provider-neutral short-video job locally with FFmpeg.

    This adapter intentionally has no network dependency. It creates a simple
    vertical MP4 from the supplied scenes, using scene text as the visual
    fallback and silence when no voice track is supplied yet.
    """

    name = "ffmpeg-local"

    def __init__(self, output_dir: str | None = None, ffmpeg_bin: str | None = None):
        self.output_dir = Path(output_dir or os.getenv("VIDEO_OUTPUT_DIR", "tmp/rendered"))
        self.ffmpeg_bin = ffmpeg_bin or os.getenv("FFMPEG_BIN", "ffmpeg")

    def submit(self, render_job: dict[str, Any]) -> dict[str, Any]:
        executable = shutil.which(self.ffmpeg_bin) or self.ffmpeg_bin
        if not shutil.which(executable) and not Path(executable).exists():
            raise RuntimeError(f"FFmpeg executable not found: {self.ffmpeg_bin}")

        scenes = render_job.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            raise ValueError("render_job.scenes must be a non-empty list")

        width, height = 720, 1280
        fps = 30
        title = str(render_job.get("title") or "casehunter-video").strip()
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in title).strip("_") or "video"

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output = self.output_dir / f"{safe_name}.mp4"
        concat_file = self.output_dir / f"{safe_name}.concat.txt"
        scene_dir = self.output_dir / f"{safe_name}_scenes"
        scene_dir.mkdir(parents=True, exist_ok=True)

        scene_files: list[Path] = []
        try:
            for index, scene in enumerate(scenes, start=1):
                duration = max(1, int(scene.get("duration_seconds", 5)))
                text = str(scene.get("on_screen_text") or scene.get("voiceover") or "").replace("'", "\\'")
                scene_file = scene_dir / f"scene_{index}.mp4"

                vf = (
                    f"drawtext=text='{text}':x=(w-text_w)/2:y=(h-text_h)/2:"
                    "fontsize=42:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=24"
                )
                cmd = [
                    executable, "-y",
                    "-f", "lavfi", "-i", f"color=c=0x111827:s={width}x{height}:r={fps}:d={duration}",
                    "-vf", vf,
                    "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration}",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(scene_file),
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                scene_files.append(scene_file)

            concat_file.write_text("".join(f"file '{p.resolve()}'\\n" for p in scene_files), encoding="utf-8")
            cmd = [
                executable, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c", "copy", str(output),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            return {
                "provider": self.name,
                "status": "rendered",
                "job": render_job,
                "output_path": str(output),
            }
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip().splitlines()[-8:]
            raise RuntimeError("FFmpeg render failed: " + " | ".join(detail)) from exc
        finally:
            shutil.rmtree(scene_dir, ignore_errors=True)
            concat_file.unlink(missing_ok=True)
