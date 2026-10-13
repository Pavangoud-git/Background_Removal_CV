
"""Image background-removal and compositing helpers."""

from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageColor, ImageOps
from requests.exceptions import ConnectionError as RequestConnectionError
from rembg import new_session, remove
from rembg.sessions.base import BaseSession


class BackgroundModelDownloadError(RuntimeError):
    """Raised when rembg cannot download its model on first use."""


@lru_cache(maxsize=1)
def _get_rembg_session() -> BaseSession:
    """Load the lightweight model once and reuse it for each image."""
    return new_session("u2netp")


def remove_background(image_bytes: bytes) -> bytes:
    """Remove the background and return a transparent PNG."""

    if not image_bytes:
        raise ValueError("The uploaded image is empty.")

    try:
        result = remove(image_bytes, session=_get_rembg_session())
    except RequestConnectionError as error:
        raise BackgroundModelDownloadError(
            "The background-removal model is not available locally, and "
            "rembg could not download it from GitHub. Reconnect to the "
            "internet, check that your network or firewall allows access "
            "to github.com, then try again. After the first successful "
            "download, the model is cached for future offline use."
        ) from error

    # Ensure the output is an RGBA PNG.
    with Image.open(BytesIO(result)) as image:
        rgba_image = image.convert("RGBA")

        output = BytesIO()
        rgba_image.save(output, format="PNG")

        return output.getvalue()


def replace_with_color(
    foreground_png: bytes,
    color_hex: str
) -> bytes:
    """Place the subject over a solid background color."""

    with Image.open(BytesIO(foreground_png)) as image:
        foreground = image.convert("RGBA")

    rgb = ImageColor.getrgb(color_hex)

    background = Image.new(
        "RGBA",
        foreground.size,
        (*rgb, 255)
    )

    result = Image.alpha_composite(
        background,
        foreground
    )

    output = BytesIO()
    result.save(output, format="PNG")

    return output.getvalue()


def replace_with_image(
    foreground_png: bytes,
    background_bytes: bytes
) -> bytes:
    """Place the subject over another background image."""

    with Image.open(BytesIO(foreground_png)) as image:
        foreground = image.convert("RGBA")

    with Image.open(BytesIO(background_bytes)) as image:
        background_source = image.convert("RGB")

        background = ImageOps.fit(
            background_source,
            foreground.size,
            method=Image.Resampling.LANCZOS
        ).convert("RGBA")

    result = Image.alpha_composite(
        background,
        foreground
    )

    output = BytesIO()
    result.save(output, format="PNG")

    return output.getvalue()