from boto.s3.bucket import Bucket
from cStringIO import StringIO
import dateutil.parser
from dateutil.tz import tzlocal
from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage

from .models import s3_conn, s3_public_conn

class S3StaticFileStorage(Storage):
    BUCKET_NAME = settings.S3_STATICFILES_BUCKET
    KEY_POLICY = 'public-read'
    CHUNK_SIZE = 100 << 20

    def __init__(self):
        super(S3StaticFileStorage, self).__init__()
        self._bucket = Bucket(connection=s3_conn, name=self.BUCKET_NAME)
        self._bucket_public = Bucket(connection=s3_public_conn,
                name=self.BUCKET_NAME)

    def _get_key(self, name):
        key = self._bucket.get_key(name)
        if key is None:
            raise IOError('No such key')
        return key

    def _open(self, name, mode='rb'):
        if mode not in ('r', 'rb'):
            raise IOError('_open() only supports reading')
        key = self._get_key(name)
        key.open_read()
        return File(key)

    def _save(self, name, content):
        hdrs = {
            'Content-Type': getattr(content, 'content_type',
                    'application/octet-stream')
        }
        if content.size > self.CHUNK_SIZE:
            # Upload in chunks
            upload = self._bucket.initiate_multipart_upload(name,
                    policy=self.KEY_POLICY, headers=hdrs)
            for i, buf in enumerate(content.chunks(self.CHUNK_SIZE), 1):
                upload.upload_part_from_file(StringIO(buf), i)
            upload.complete_upload()
        else:
            # Upload all at once
            key = self._bucket.new_key(name)
            key.set_contents_from_string(content.read(),
                    policy=self.KEY_POLICY, headers=hdrs)
        return name

    def get_available_name(self, name):
        return name

    def get_valid_name(self, name):
        return name

    def delete(self, name):
        self._bucket.delete_key(name)

    def exists(self, name):
        key = self._bucket.get_key(name)
        return key is not None

    def listdir(self, path):
        path = path.lstrip('/')
        return ([], [key.name for key in self._bucket.list(prefix=path)])

    def modified_time(self, name):
        key = self._get_key(name)
        stamp = dateutil.parser.parse(key.last_modified)
        # Convert to naive datetime in local time, as FileSystemStorage does
        return stamp.astimezone(tzlocal()).replace(tzinfo=None)

    def size(self, name):
        key = self._get_key(name)
        return key.size

    def url(self, name):
        key = self._bucket_public.new_key(name)
        return key.generate_url(0, query_auth=False)
