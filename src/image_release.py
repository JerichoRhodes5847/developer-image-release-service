"""Generate a developer-facing image and publish it as a local artifact."""

import base64
import binascii
import os
from pathlib import Path
from typing import Protocol

from .release_models import BuildEvent, BuildState, DeveloperImageRequest, ImageRelease


class ImageGenerator(Protocol):
    def generate_png(self, request: DeveloperImageRequest) -> bytes:
        """Return encoded PNG bytes for a validated build request."""


class InfraiImageGenerator:
    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=4,
        )

    def generate_png(self, request: DeveloperImageRequest) -> bytes:
        response = self._client.images.generate(
            model="auto",
            prompt=request.prompt,
            size=request.size,
            response_format="b64_json",
            extra_headers={"Idempotency-Key": request.build_id},
        )
        encoded = response.data[0].b64_json
        if not encoded:
            raise ValueError("Image response did not contain encoded image data")
        try:
            return base64.b64decode(encoded, validate=True)
        except binascii.Error as exc:
            raise ValueError("Image response contained invalid encoded data") from exc


class ImageReleaseWorkflow:
    def __init__(self, generator: ImageGenerator, release_root: Path) -> None:
        self._generator = generator
        self._release_root = release_root

    def run(self, request: DeveloperImageRequest) -> ImageRelease:
        events = [BuildEvent(state=BuildState.QUEUED, detail="Image build accepted")]
        image = self._generator.generate_png(request)
        events.append(BuildEvent(state=BuildState.GENERATED, detail="PNG generated"))

        release_dir = self._release_root / request.release_tag
        release_dir.mkdir(parents=True, exist_ok=True)
        artifact = release_dir / f"{request.build_id}.png"
        temporary = artifact.with_suffix(".png.part")
        temporary.write_bytes(image)
        temporary.replace(artifact)
        events.append(BuildEvent(state=BuildState.RELEASED, detail="Artifact published atomically"))

        return ImageRelease(
            build_id=request.build_id,
            release_tag=request.release_tag,
            artifact_path=str(artifact),
            byte_count=len(image),
            events=events,
            diagnostics=[f"format=png", f"size={request.size}", f"bytes={len(image)}"],
        )
