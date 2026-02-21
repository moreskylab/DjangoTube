from imagekitio import ImageKit
from django.conf import settings
import base64

imagekit = ImageKit()


def upload_to_imagekit(file_obj, file_name):
    """
    Uploads a file object to ImageKit.
    Returns the response dict containing url, fileId, thumbnail, etc.
    """
    # Convert file to base64 or bytes for SDK
    file_bytes = file_obj.read()

    upload = imagekit.files.upload(
        file=file_bytes,
        file_name=file_name,
        public_key=settings.IMAGEKIT_PUBLIC_KEY
    )
    return upload