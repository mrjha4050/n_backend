# n_backend/app/cloudinary.py
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


def upload_image(file_obj, folder=None, resource_type='image', overwrite=False):
    """
    Upload an image to Cloudinary

    Args:
        file_obj: The file object to upload
        folder: The folder path in Cloudinary (optional)
        resource_type: Type of resource ('image', 'video', etc.)
        overwrite: Whether to overwrite existing files

    Returns:
        dict: Cloudinary upload response
    """
    try:
        upload_options = {
            'resource_type': resource_type,
            'overwrite': overwrite,
        }

        if folder:
            upload_options['folder'] = folder

        result = cloudinary.uploader.upload(file_obj, **upload_options)
        return result

    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        raise e


def upload_image_from_url(image_url, folder=None, resource_type='image'):
    """
    Upload an image from URL to Cloudinary

    Args:
        image_url: URL of the image to upload
        folder: The folder path in Cloudinary (optional)
        resource_type: Type of resource

    Returns:
        dict: Cloudinary upload response
    """
    try:
        upload_options = {
            'resource_type': resource_type,
        }

        if folder:
            upload_options['folder'] = folder

        result = cloudinary.uploader.upload(image_url, **upload_options)
        return result

    except Exception as e:
        print(f"Cloudinary upload from URL error: {str(e)}")
        raise e


def delete_image(public_id, resource_type='image'):
    """
    Delete an image from Cloudinary

    Args:
        public_id: The public ID of the image
        resource_type: Type of resource

    Returns:
        dict: Cloudinary delete response
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result
    except Exception as e:
        print(f"Cloudinary delete error: {str(e)}")
        raise e


def get_image_url(public_id, transformation=None, format=None):
    """
    Generate Cloudinary URL for an image

    Args:
        public_id: The public ID of the image
        transformation: Cloudinary transformation options (optional)
        format: Image format (optional)

    Returns:
        str: Image URL
    """
    try:
        url_options = {}
        if transformation:
            url_options['transformation'] = transformation
        if format:
            url_options['format'] = format

        url = cloudinary.CloudinaryImage(public_id).build_url(**url_options)
        return url
    except Exception as e:
        print(f"Cloudinary URL generation error: {str(e)}")
        raise e