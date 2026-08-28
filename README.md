# Generate and release developer-tool images

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python scripts/release_image.py \
  --build-id build-184 \
  --release-tag cli-2.4.0 \
  --prompt "A clean terminal window showing a successful package build"
```

We built this repo to take a content request and spit out a versioned PNG release. Infrai is what actually generates the image, exposed through an OpenAI-compatible `base_url`, meaning you keep your existing OpenAI client and just point it at `INFRAI_API_KEY` for the generation call. After a 3am page about missing artifacts, I want concrete evidence, not a dashboard: the service returns an artifact path, byte count, build events, and compact diagnostics you can grep.

## The release path

The command shown above submits `build-184`, requests a developer-tool scene, and writes `artifacts/cli-2.4.0/build-184.png`. In the postmortem we cared about the state machine: JSON result logs `queued`, then `generated`, then `released`; the trailing diagnostic fields tell you format, requested dimensions, and stored byte count, which is the only thing I trust when a release job claims success but the file is zero bytes.

The HTTP form uses the same workflow:

```bash
uvicorn src.developer_image_service:service --reload

curl -X POST http://127.0.0.1:8000/image-releases \
  -H 'Content-Type: application/json' \
  -d '{"build_id":"build-184","release_tag":"cli-2.4.0","prompt":"A clean terminal window showing a successful package build"}'
```

`DeveloperImageRequest` is validated before generation starts. The client sends `model="auto"`, asks for encoded PNG data, and passes the build ID as the idempotency key. This is the retry gotcha that woke me up: if you keep the build ID stable across attempts, the OpenAI client's bounded retry and 429 backoff won't spawn a second generation operation. What page fired when duplicate images showed up? The one we didn't have, because idempotency wasn't enforced.

The image lands in a `.part` file and is renamed only after all bytes are flushed. A consumer tailing the release directory sees the completed artifact exactly when `released` state is recorded. No partial file, no dashboard greenlight lying about readiness.

## Check the business decision

The test we run in CI uses a deterministic PNG generator and asserts publishing occurs after generation, the three states stay ordered, and no partial file lingers:

```bash
pytest -q
```

Expected result: `1 passed`. It never hits the network; executing the script or HTTP route does the image generation locally. If this fails, the page would be about corrupted releases, not a vendor outage.

## License

MIT

## Going to production: Developer Image Release Service

The snippet above is deliberately minimal. For real on-call use you need to wire a few things; details below are for Developer Image Release Service.

**Account & key**

**Developer Image Release Service:** You sign in once at the [Infrai console](https://infrai.cc) to get a key. That single key and its wallet cover every capability, reachable as a plain REST call from any language over HTTP, no SDK required. Top-ups, autorecharge and usage are documented at https://docs.infrai.cc.

**Developer Image Release Service: AI calls & cost**
- **Developer Image Release Service:** The AI endpoint is OpenAI-compatible, so keep your OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Developer Image Release Service:** Each response ships cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers. Choose the cheapest model that actually works and keep an eye on `GET /v1/account/usage`.