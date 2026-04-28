#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pillow>=10.0.0",
#     "python-dotenv>=1.0.0",
# ]
# ///
"""
Generate images using Google Gemini image models.

Supported models:
  - gemini-3.1-flash-image-preview (alias: flash) — Nano Banana 2, fast (default)
  - gemini-3-pro-image-preview     (alias: pro)   — Nano Banana Pro, high quality, 2K/4K

Usage:
    uv run generate_image.py --prompt "description" --filename "output.png"
    uv run generate_image.py --prompt "description" --filename "output.png" --model flash
    uv run generate_image.py --prompt "description" --filename "output.png" --model flash --aspect-ratio 16:9

Multi-image editing (up to 14 images):
    uv run generate_image.py --prompt "combine these" --filename "output.png" -i img1.png -i img2.png
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from skill directory or workspace root
_script_dir = Path(__file__).resolve().parent
for _candidate in [_script_dir, _script_dir.parent, _script_dir.parent.parent, _script_dir.parent.parent.parent, Path.cwd()]:
    _env_file = _candidate / ".env"
    if _env_file.is_file():
        load_dotenv(_env_file)
        break

# Model aliases → full model IDs
MODEL_ALIASES: dict[str, str] = {
    "pro": "gemini-3-pro-image-preview",
    "flash": "gemini-3.1-flash-image-preview",
}

VALID_RESOLUTIONS = {"1K", "2K", "4K"}
VALID_ASPECT_RATIOS = {"1:1", "16:9", "9:16", "4:3", "3:4"}
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"


def resolve_model(name: str) -> str:
    """Resolve alias or full model name."""
    return MODEL_ALIASES.get(name, name)


def get_api_key(provided_key: str | None) -> str | None:
    """Get API key from argument first, then environment."""
    if provided_key:
        return provided_key
    return os.environ.get("GEMINI_API_KEY")


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini image models"
    )
    parser.add_argument(
        "--prompt", "-p", required=True,
        help="Image description/prompt"
    )
    parser.add_argument(
        "--filename", "-f", required=True,
        help="Output filename (e.g., sunset-mountains.png)"
    )
    parser.add_argument(
        "--model", "-m", default=DEFAULT_MODEL,
        help=f"Model name or alias. Aliases: {', '.join(f'{k}={v}' for k, v in MODEL_ALIASES.items())}. Default: {DEFAULT_MODEL}"
    )
    parser.add_argument(
        "--input-image", "-i", action="append", dest="input_images", metavar="IMAGE",
        help="Input image path(s) for editing/composition. Can be specified multiple times (up to 14)."
    )
    parser.add_argument(
        "--resolution", "-r", choices=sorted(VALID_RESOLUTIONS), default="1K",
        help="Output resolution: 1K (default), 2K, or 4K"
    )
    parser.add_argument(
        "--aspect-ratio", "-a", choices=sorted(VALID_ASPECT_RATIOS), default=None,
        help="Aspect ratio (e.g., 16:9, 9:16, 4:3). Default: model default"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="Gemini API key (overrides GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--proxy",
        help="HTTPS proxy URL (overrides HTTPS_PROXY env var)"
    )

    args = parser.parse_args()

    # Resolve model
    model = resolve_model(args.model)
    print(f"Using model: {model}")

    # Get API key
    api_key = get_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided.", file=sys.stderr)
        print("Please either:", file=sys.stderr)
        print("  1. Provide --api-key argument", file=sys.stderr)
        print("  2. Set GEMINI_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    # Import here after checking API key to avoid slow import on error
    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    # Set up proxy if provided
    proxy = args.proxy or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        os.environ["HTTPS_PROXY"] = proxy
        os.environ["HTTP_PROXY"] = proxy
        print(f"Using proxy: {proxy}")

    # Initialise client
    client = genai.Client(api_key=api_key)

    # Set up output path
    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load input images if provided
    input_images = []
    output_resolution = args.resolution
    if args.input_images:
        if len(args.input_images) > 14:
            print(f"Error: Too many input images ({len(args.input_images)}). Maximum is 14.", file=sys.stderr)
            sys.exit(1)

        max_input_dim = 0
        for img_path in args.input_images:
            try:
                img = PILImage.open(img_path)
                input_images.append(img)
                print(f"Loaded input image: {img_path}")
                width, height = img.size
                max_input_dim = max(max_input_dim, width, height)
            except Exception as e:
                print(f"Error loading input image '{img_path}': {e}", file=sys.stderr)
                sys.exit(1)

        # Auto-detect resolution from largest input if not explicitly set
        if args.resolution == "1K" and max_input_dim > 0:
            if max_input_dim >= 3000:
                output_resolution = "4K"
            elif max_input_dim >= 1500:
                output_resolution = "2K"
            else:
                output_resolution = "1K"
            print(f"Auto-detected resolution: {output_resolution} (from max input dimension {max_input_dim})")

    # Build image_config
    image_config_kwargs: dict = {"image_size": output_resolution}
    if args.aspect_ratio:
        image_config_kwargs["aspect_ratio"] = args.aspect_ratio

    # Build contents
    if input_images:
        contents = [*input_images, args.prompt]
        img_count = len(input_images)
        print(f"Processing {img_count} image{'s' if img_count > 1 else ''} with resolution {output_resolution}...")
    else:
        contents = args.prompt
        extra = f", aspect_ratio={args.aspect_ratio}" if args.aspect_ratio else ""
        print(f"Generating image with resolution {output_resolution}{extra}...")

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(**image_config_kwargs)
            )
        )

        # Process response
        image_saved = False
        for part in response.parts:
            if part.text is not None:
                print(f"Model response: {part.text}")
            elif part.inline_data is not None:
                # Try the newer as_image() API first, fall back to manual decode
                try:
                    image = part.as_image()
                except AttributeError:
                    from io import BytesIO
                    import base64
                    image_data = part.inline_data.data
                    if isinstance(image_data, str):
                        image_data = base64.b64decode(image_data)
                    image = PILImage.open(BytesIO(image_data))

                # Ensure RGB for PNG output
                if image.mode == 'RGBA':
                    rgb_image = PILImage.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])
                    rgb_image.save(str(output_path), 'PNG')
                elif image.mode == 'RGB':
                    image.save(str(output_path), 'PNG')
                else:
                    image.convert('RGB').save(str(output_path), 'PNG')
                image_saved = True

        if image_saved:
            full_path = output_path.resolve()
            print(f"\nImage saved: {full_path}")
            print(f"MEDIA: {full_path}")
        else:
            print("Error: No image was generated in the response.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
