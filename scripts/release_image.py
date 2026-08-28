"""Run one developer image release without starting the HTTP service."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.image_release import ImageReleaseWorkflow, InfraiImageGenerator
from src.release_models import DeveloperImageRequest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    request = DeveloperImageRequest(
        build_id=args.build_id,
        release_tag=args.release_tag,
        prompt=args.prompt,
    )
    result = ImageReleaseWorkflow(InfraiImageGenerator(), args.output).run(request)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
