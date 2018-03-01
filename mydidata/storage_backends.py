from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class PublicMediaStorage(S3Boto3Storage):
    location = settings.UPLOAD_URL

    def _clean_name(self, name):
        return name

    def _normalize_name(self, name):
        if not name.endswith('/'):
            name += "/"

        name += self.location
        return name

    
    file_overwrite = True