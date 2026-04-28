---
name: nano-banana-pro
description: Generate or edit images via Gemini image models (Nano Banana 2 / Nano Banana Pro). Supports model selection.
homepage: https://ai.google.dev/
metadata:
  {
    "openclaw":
      {
        "emoji": "🍌",
        "requires": { "bins": ["uv"], "env": ["GEMINI_API_KEY"] },
        "primaryEnv": "GEMINI_API_KEY",
        "install":
          [
            {
              "id": "uv-brew",
              "kind": "brew",
              "formula": "uv",
              "bins": ["uv"],
              "label": "Install uv (brew)",
            },
          ],
      },
  }
---

# Nano Banana Pro (Gemini Image Generation)

Use the bundled script to generate or edit images with selectable models.

## Available Models

| Model ID | Alias | Description |
|---|---|---|
| `gemini-3.1-flash-image-preview` | `flash` | Nano Banana 2 — fast, good quality (default) |
| `gemini-3-pro-image-preview` | `pro` | Nano Banana Pro — high quality, supports 2K/4K, up to 14 input images |

Default model: `gemini-3.1-flash-image-preview` (alias `flash`)

## Usage

Generate

```bash
uv run {baseDir}/scripts/generate_image.py --prompt "your image description" --filename "output.png"
```

Generate with model selection

```bash
uv run {baseDir}/scripts/generate_image.py --prompt "your image description" --filename "output.png" --model flash
uv run {baseDir}/scripts/generate_image.py --prompt "your image description" --filename "output.png" --model pro
```

Generate with resolution, aspect ratio, and proxy

```bash
uv run {baseDir}/scripts/generate_image.py --prompt "a landscape" --filename "output.png" --model pro --resolution 2K --aspect-ratio 16:9
uv run {baseDir}/scripts/generate_image.py --prompt "a landscape" --filename "output.png" --proxy http://127.0.0.1:7890
```

Edit (single image)

```bash
uv run {baseDir}/scripts/generate_image.py --prompt "edit instructions" --filename "output.png" -i "/path/in.png" --model pro --resolution 2K
```

Multi-image composition (up to 14 images, pro model)

```bash
uv run {baseDir}/scripts/generate_image.py --prompt "combine these into one scene" --filename "output.png" --model pro -i img1.png -i img2.png -i img3.png
```

## API key

- `GEMINI_API_KEY` env var
- Or set `skills."nano-banana-pro".apiKey` / `skills."nano-banana-pro".env.GEMINI_API_KEY` in `~/.openclaw/openclaw.json`

## Proxy

- `HTTPS_PROXY` env var (in `.env` or system environment)
- Or pass `--proxy http://127.0.0.1:7890` on the command line

## Notes

- Resolutions: `1K` (default), `2K`, `4K` (only `pro` model supports 4K).
- Aspect ratios: `1:1` (default), `16:9`, `9:16`, `4:3`, `3:4`.
- Use timestamps in filenames: `yyyy-mm-dd-hh-mm-ss-name.png`.
- The script prints a `MEDIA:` line for OpenClaw to auto-attach on supported chat providers.
- Do not read the image back; report the saved path only.
