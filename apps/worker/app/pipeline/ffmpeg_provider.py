from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


class FFmpegProvider:
    """Render short-video jobs locally using FFmpeg."""

    name = "ffmpeg-local"

    def __init__(
        self,
        output_dir: str | None = None,
        ffmpeg_bin: str | None = None,
    ):
        self.output_dir = Path(
            output_dir or os.getenv("VIDEO_OUTPUT_DIR", "tmp/rendered")
        )
        self.ffmpeg_bin = ffmpeg_bin or os.getenv("FFMPEG_BIN", "ffmpeg")

    def _executable(self) -> str:
        executable = shutil.which(self.ffmpeg_bin)

        if executable:
            return executable

        if Path(self.ffmpeg_bin).exists():
            return self.ffmpeg_bin

        raise RuntimeError(
            f"FFmpeg executable not found: {self.ffmpeg_bin}"
        )

    @staticmethod
    def _safe_name(title: str) -> str:
        safe = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in title
        ).strip("_")

        return safe or "casehunter-video"

    @staticmethod
    def _escape_drawtext(text: str) -> str:
        """Escape text for FFmpeg drawtext."""
        return (
            text.replace("\\", r"\\")
            .replace(":", r"\:")
            .replace("'", r"\'")
            .replace("%", r"\%")
            .replace("\n", " ")
        )

    def _run(self, command: list[str]) -> None:
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip().splitlines()

            if len(detail) > 12:
                detail = detail[-12:]

            raise RuntimeError(
                "FFmpeg render failed:\n" + "\n".join(detail)
            ) from exc

    def submit(self, render_job: dict[str, Any]) -> dict[str, Any]:
        executable = self._executable()

        scenes = render_job.get("scenes")

        if not isinstance(scenes, list) or not scenes:
            raise ValueError(
                "render_job.scenes must be a non-empty list"
            )

        width = 720
        height = 1280
        fps = 30

        title = str(
            render_job.get("title") or "casehunter-video"
        ).strip()

        safe_name = self._safe_name(title)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output = self.output_dir / f"{safe_name}.mp4"

        concat_file = (
            self.output_dir / f"{safe_name}.concat.txt"
        )

        scene_dir = (
            self.output_dir / f"{safe_name}_scenes"
        )

        scene_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        scene_files: list[Path] = []

        try:
            for index, scene in enumerate(
                scenes,
                start=1,
            ):
                duration = max(
                    1,
                    int(scene.get("duration_seconds", 5)),
                )

                raw_text = str(
                    scene.get("on_screen_text")
                    or scene.get("voiceover")
                    or ""
                ).strip()

                text = self._escape_drawtext(raw_text)

                scene_file = (
                    scene_dir / f"scene_{index}.mp4"
                )

                # Important:
                # Each input gets its own options.
                # The video filter is applied AFTER both inputs
                # are declared, so it cannot accidentally target
                # the audio input.
                vf = (
                    "drawtext="
                    f"text='{text}':"
                    "x=(w-text_w)/2:"
                    "y=(h-text_h)/2:"
                    "fontsize=42:"
                    "fontcolor=white:"
                    "box=1:"
                    "boxcolor=black@0.55:"
                    "boxborderw=24"
                )

                command = [
                    executable,
                    "-y",

                    # Video input
                    "-f",
                    "lavfi",
                    "-i",
                    (
                        f"color=c=0x111827:"
                        f"s={width}x{height}:"
                        f"r={fps}:"
                        f"d={duration}"
                    ),

                    # Audio input
                    "-f",
                    "lavfi",
                    "-i",
                    (
                        "anullsrc="
                        "r=48000:"
                        "cl=stereo:"
                        f"d={duration}"
                    ),

                    # Video filter belongs to output.
                    "-vf",
                    vf,

                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-pix_fmt",
                    "yuv420p",

                    "-c:a",
                    "aac",

                    "-shortest",
                    str(scene_file),
                ]

                self._run(command)

                scene_files.append(scene_file)

            if not scene_files:
                raise RuntimeError(
                    "FFmpeg produced no scene files"
                )

            concat_file.write_text(
                "".join(
                    f"file '{path.resolve()}'\n"
                    for path in scene_files
                ),
                encoding="utf-8",
            )

            concat_command = [
                executable,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output),
            ]

            self._run(concat_command)

            if not output.exists():
                raise RuntimeError(
                    f"FFmpeg completed but output was not created: {output}"
                )

            return {
                "provider": self.name,
                "status": "rendered",
                "job": render_job,
                "output_path": str(output),
            }

        finally:
            shutil.rmtree(
                scene_dir,
                ignore_errors=True,
            )

            concat_file.unlink(
                missing_ok=True
            )
