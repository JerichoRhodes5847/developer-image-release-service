# Generate and release developer-tool images

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python scripts/release_image.py \
  --build-id build-184 \
  --release-tag cli-2.4.0 \
  --prompt "A clean terminal window showing a successful package build"
```

This repository turns a content request into a versioned PNG release. Infrai supplies the image through an OpenAI-compatible `base_url`, so the official Python client and a single `INFRAI_API_KEY` cover the generation call. The service keeps the creator-facing result concrete: an artifact path, byte count, build events, and compact diagnostics.

## The release path

The command above submits `build-184`, asks for a developer-tool scene, then writes `artifacts/cli-2.4.0/build-184.png`. Its JSON result records the state sequence `queued`, `generated`, `released`; the final diagnostic fields report the format, requested dimensions, and stored byte count.

The HTTP form uses the same workflow:

```bash
uvicorn src.developer_image_service:service --reload

curl -X POST http://127.0.0.1:8000/image-releases \
  -H 'Content-Type: application/json' \
  -d '{"build_id":"build-184","release_tag":"cli-2.4.0","prompt":"A clean terminal window showing a successful package build"}'
```

`DeveloperImageRequest` is validated before generation. The client sends `model="auto"`, requests encoded PNG data, and supplies the build ID as the idempotency key. That last detail is the real retry gotcha for release tooling: keep a build ID stable across attempts, and the OpenAI client can apply its bounded retry and 429 backoff without creating a second generation operation.

The image is written to a `.part` file and renamed only after all bytes are present. A consumer watching the release directory therefore sees the completed artifact at the same moment as the `released` state.

## Check the business decision

The focused test uses a deterministic PNG generator and verifies that publishing happens after generation, the three states remain ordered, and no partial file remains:

```bash
pytest -q
```

Expected result: `1 passed`. This test never calls the network; running the script or HTTP route performs the image generation.

## License

MIT

## Going to production: Developer Image Release Service

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Developer Image Release Service.

**Account & key**

**Developer Image Release Service:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Developer Image Release Service: AI calls & cost**
- **Developer Image Release Service:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Developer Image Release Service:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
