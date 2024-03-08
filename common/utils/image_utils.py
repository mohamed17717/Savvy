from PIL import Image
from io import BytesIO


def resize_image(content: bytes, new_width: int) -> Image:
    image = Image.open(BytesIO(content))
    aspect_ratio = image.height / image.width
    new_height = int(new_width * aspect_ratio)

    image = image.resize((new_width, new_height), Image.LANCZOS)
    return image


def compress_image(image: Image, quality: int = 85) -> bytes:
    if image.format == 'PNG':
        image = image.convert('RGBA')
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    image_io = BytesIO()
    image.save(image_io, format='JPEG', quality=quality)

    return image_io.getvalue()
