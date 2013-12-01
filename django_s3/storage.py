#
# Copyright (C) 2013 Carnegie Mellon University
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from boto.s3.bucket import Bucket
from boto.s3.cors import CORSConfiguration
from cStringIO import StringIO
import dateutil.parser
from dateutil.tz import tzlocal
from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
import magic

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

        # Allow CORS access from this app (for web fonts)
        self._bucket.set_cors(self._get_cors_config())

    def _get_cors_config(self):
        origins = []
        for host in settings.ALLOWED_HOSTS:
            for scheme in ('http', 'https'):
                origins.append('%s://%s' % (scheme, host))
        cors = CORSConfiguration()
        cors.add_rule(['GET'], origins)
        return cors

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
        if name.endswith('.css'):
            content_type = 'text/css'
        elif name.endswith('.js'):
            content_type = 'application/javascript'
        elif name.endswith('.json'):
            content_type = 'application/json'
        elif hasattr(content.file, 'getvalue'):
            content_type = magic.from_buffer(content.file.getvalue(),
                    mime=True)
        else:
            content_type = magic.from_file(content.file.name, mime=True)
        hdrs = {
            'Content-Type': content_type,
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


class S3CompressedFileStorage(S3StaticFileStorage):
    '''Storage class that makes a local copy of the files for
    django_compressor.'''

    def __init__(self, *args, **kwargs):
        from compressor.storage import CompressorFileStorage
        super(S3CompressedFileStorage, self).__init__(*args, **kwargs)
        self._local_storage = CompressorFileStorage()

    def save(self, name, content):
        name = super(S3CompressedFileStorage, self).save(name, content)
        self._local_storage._save(name, content)
        return name
