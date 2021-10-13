import os


def get_course_upload_path(instance, filename):
    return os.path.join(
        'courses',
        str(instance.slug),
        filename
    )


def get_item_file_upload_path(instance, filename):
    return os.path.join(
        'item-file',
        filename
    )


def get_item_image_upload_path(instance, filename):
    return os.path.join(
        'item-image',
        filename
    )