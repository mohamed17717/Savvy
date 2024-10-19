import base64
import logging
from io import BytesIO
from urllib.parse import urlparse

import cairosvg
import requests
from PIL import Image

logger = logging.getLogger(__name__)


def resize_image(content: bytes, new_width: int) -> Image:
    image = Image.open(BytesIO(content))
    aspect_ratio = image.height / image.width
    new_height = int(new_width * aspect_ratio)

    image = image.resize((new_width, new_height), Image.LANCZOS)
    return image


def compress_image(image: Image, quality: int = 85) -> bytes:
    if image.format == "PNG":
        image = image.convert("RGBA")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    image_io = BytesIO()
    image.save(image_io, format="JPEG", quality=quality)

    return image_io.getvalue()


def download_image(url: str) -> list[bytes, str]:
    content = None

    if url.startswith("data:image"):
        content = base64.b64decode(url.split(",")[-1])
        return content, None

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"  # noqa
            },
            timeout=8,
        )
        if response.status_code == 200:
            content = response.content
            if urlparse(url).path.endswith(".svg"):
                content = cairosvg.svg2png(content, output_width=300)

        elif not 400 <= response.status_code < 410:
            response.raise_for_status()
    except (
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.InvalidURL,
    ) as e:
        # its not an error image is not exist at all
        logger.error(e)

    return content, url
