import os


def get_account_upload_path(instance, filename):
    return os.path.join(
        'accounts',
        filename
    )
