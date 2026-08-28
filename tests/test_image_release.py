from pathlib import Path

from src.image_release import ImageReleaseWorkflow
from src.release_models import BuildState, DeveloperImageRequest


class FixedGenerator:
    def generate_png(self, request: DeveloperImageRequest) -> bytes:
        return b"\x89PNG\r\n\x1a\nrelease-image"


def test_release_publishes_image_after_generation(tmp_path: Path) -> None:
    request = DeveloperImageRequest(
        build_id="build-184",
        release_tag="cli-2.4.0",
        prompt="A clean terminal window showing a successful package build",
    )

    result = ImageReleaseWorkflow(FixedGenerator(), tmp_path).run(request)

    artifact = tmp_path / "cli-2.4.0" / "build-184.png"
    assert artifact.read_bytes().startswith(b"\x89PNG")
    assert result.artifact_path == str(artifact)
    assert [event.state for event in result.events] == [
        BuildState.QUEUED,
        BuildState.GENERATED,
        BuildState.RELEASED,
    ]
    assert not artifact.with_suffix(".png.part").exists()
