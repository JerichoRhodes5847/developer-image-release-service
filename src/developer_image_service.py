"""Application-shaped HTTP entry point for image builds."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError

from .image_release import ImageReleaseWorkflow, InfraiImageGenerator
from .release_models import DeveloperImageRequest, ImageRelease

service = FastAPI(title="Developer Image Release Service")


def release_workflow() -> ImageReleaseWorkflow:
    root = Path(os.environ.get("IMAGE_RELEASE_DIR", "artifacts"))
    return ImageReleaseWorkflow(InfraiImageGenerator(), root)


@service.post("/image-releases", response_model=ImageRelease, status_code=201)
def create_image_release(request: DeveloperImageRequest) -> ImageRelease:
    try:
        return release_workflow().run(request)
    except APIStatusError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail="Image generation request was rejected") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=502, detail="Image generation transport error") from exc
