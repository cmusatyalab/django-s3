#
# Copyright (C) 2012-2013 Carnegie Mellon University
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

import base64
import boto, boto.s3.bucket, boto.s3.connection, boto.s3.multipart
from cStringIO import StringIO
from django.conf import settings
from django.db import models
from django.utils.http import http_date
from hashlib import sha256
from itertools import count
import os
import time

s3_conn = boto.connect_s3(host=settings.S3_HOST,
        port=getattr(settings, 'S3_PORT', None),
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        is_secure=getattr(settings, 'S3_SECURE_CONN', True),
        calling_format=boto.s3.connection.OrdinaryCallingFormat())
if getattr(settings, 'S3_PUBLIC_HOST', None):
    s3_public_conn = boto.connect_s3(host=settings.S3_PUBLIC_HOST,
            port=getattr(settings, 'S3_PUBLIC_PORT', None),
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            is_secure=getattr(settings, 'S3_PUBLIC_SECURE_CONN', True),
            calling_format=boto.s3.connection.OrdinaryCallingFormat())
else:
    s3_public_conn = s3_conn


class DataCorruption(Exception):
    def __init__(self, msg, expected, found):
        Exception.__init__(self, msg)
        self.expected = expected
        self.found = found


class Container(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.name

    @property
    def bucket(self):
        if not getattr(self, '_bucket', None):
            self._bucket = boto.s3.bucket.Bucket(connection=s3_conn,
                    name=self.name)
        return self._bucket

    @classmethod
    def get(cls, container_type):
        container_name = settings.S3_BUCKETS[container_type]
        return cls.objects.get_or_create(name=container_name)[0]


class Blob(models.Model):
    CHUNK_SIZE = 100 << 20

    class Meta:
        unique_together = (('container', 'name'),)

    container = models.ForeignKey(Container)
    name = models.CharField(max_length=44, default=lambda:
            base64.urlsafe_b64encode(os.urandom(33)))
    content_type = models.CharField(max_length=80,
            default='application/octet-stream')
    size = models.BigIntegerField(null=True)
    sha256 = models.CharField(verbose_name='SHA-256', max_length=64,
            blank=True)
    upload_id = models.CharField(max_length=100, blank=True)
    complete = models.BooleanField()

    def __unicode__(self):
        return '%s/%s (%s)' % (self.container, self.name,
                self.sha256 or '<unknown SHA-256>')

    @property
    def key(self):
        if not getattr(self, '_key', None):
            self._key = self.container.bucket.new_key(self.name)
        return self._key

    def delete(self, *args, **kwargs):
        self.remove()
        super(Blob, self).delete(*args, **kwargs)

    def get(self, fh=None, offset=0, length=None):
        if not self.complete:
            raise ValueError('Blob not complete')
        hdrs = {}
        if length == 0:
            return
        elif length is not None:
            hdrs['Range'] = 'bytes=%d-%d' % (offset, offset + length - 1)
        elif offset:
            hdrs['Range'] = 'bytes=%d-' % offset
        if fh is not None:
            self.key.get_contents_to_file(fh, headers=hdrs)
        else:
            self.key.open_read(headers=hdrs)
            return self.key

    def make_url(self, content_disposition=None, refresh=getattr(settings,
            'S3_SIGNED_URL_REFRESH_INTERVAL', 3600 * 8),
            grace=getattr(settings, 'S3_SIGNED_URL_GRACE', 300)):
        resp_hdrs = {}
        if content_disposition is not None:
            # Assume the object is being offered for download.  Prioritize
            # security over cachability.
            expiration = int(time.time()) + grace
            resp_hdrs['response-content-disposition'] = content_disposition
        else:
            # Assume the object is being rendered inline.  Batch expirations
            # s.t. there is exactly one valid expiration date every
            # @refresh seconds.  Select the expiration date in the range
            # (@grace, @refresh + @grace].  This gives an average useful
            # cache time of (@refresh / 2) + @grace.
            expiration = (int((time.time() // refresh) * refresh) + refresh +
                    grace)
        resp_hdrs['response-expires'] = http_date(expiration)

        bucket = boto.s3.bucket.Bucket(connection=s3_public_conn,
                name=self.container.name)
        key = bucket.new_key(self.name)
        return key.generate_url(expiration, expires_in_absolute=True,
                response_headers=resp_hdrs)

    def put(self, contents):
        if self.complete:
            raise ValueError('Blob already complete')
        if self.upload_id:
            raise ValueError('Chunked upload in progress')
        hdrs = {
            'Content-Type': str(self.content_type),
        }
        if hasattr(contents, 'seek'):
            # Upload from file
            start = contents.tell()
            contents.seek(0, 2)
            size = contents.tell() - start
            contents.seek(start)
            if size > self.CHUNK_SIZE:
                # Upload in chunks
                self.start_segments()
                for i in count(1):
                    if size == 0:
                        break
                    cur = min(self.CHUNK_SIZE, size)
                    self.put_segment(i, contents, cur)
                    size -= cur
                self.commit_segments()
                # commit_segments() sets self.size
            else:
                # Upload all at once
                self.size = self.key.set_contents_from_file(contents,
                        headers=hdrs)
            contents.seek(start)
        else:
            # Upload from string
            self.key.set_contents_from_string(contents, headers=hdrs)
            self.size = len(contents)
        if not self.sha256:
            self.sha256 = self._calc_sha256(contents)
        self.complete = True
        self.save()

    def start_segments(self):
        if self.complete:
            raise ValueError('Blob already complete')
        self.remove()
        hdrs = {
            'Content-Type': str(self.content_type),
        }
        upload = self.container.bucket.initiate_multipart_upload(self.name,
                headers=hdrs)
        self.upload_id = upload.id
        self.save()

    def put_segment(self, segment_num, contents, length=None):
        if self.complete:
            raise ValueError('Blob already complete')
        if not self.upload_id:
            raise ValueError('No upload in progress')
        if not hasattr(contents, 'seek'):
            # set_contents_from_string() doesn't take query_args
            contents = StringIO(contents)
        qs = 'uploadId=%s&partNumber=%d' % (self.upload_id, segment_num)
        self.key.set_contents_from_file(contents, query_args=qs, size=length)

    def commit_segments(self):
        if self.complete:
            raise ValueError('Blob already complete')
        if not self.upload_id:
            raise ValueError('No upload in progress')
        # Manufacture a MultiPartUpload with the correct settings, since
        # we can't hold onto the object for the entire upload process
        upload = boto.s3.multipart.MultiPartUpload(self.container.bucket)
        upload.key_name = self.name
        upload.id = self.upload_id
        size = 0
        for part in upload:
            size += part.size
        upload.complete_upload()
        self.upload_id = ''
        self.size = size
        self.complete = True
        self.save()

    def set_sha256(self, contents):
        '''Set self.sha256 from contents, which MUST be a file or string
        containing the exact contents of this blob.  This is useful if the
        blob was uploaded in chunks, in which case self.sha256 was not set at
        upload time.'''
        if not self.sha256:
            self.sha256 = self._calc_sha256(contents)
            self.save()

    def check_sha256(self, contents):
        '''Check contents against self.sha256 and raise DataCorruption if
        there's a mismatch.  Raise ValueError if self.sha256 is not set.'''
        if not self.sha256:
            raise ValueError('SHA-256 is not set')
        found = self._calc_sha256(contents)
        if self.sha256 != found:
            raise DataCorruption('SHA-256 mismatch', self.sha256, found)

    def remove(self):
        # Remove object if it exists
        self.key.delete()
        # Abort upload if it exists
        if self.upload_id:
            self.container.bucket.cancel_multipart_upload(self.name,
                    self.upload_id)
        # Mark incomplete
        self.upload_id = ''
        self.size = None
        self.sha256 = ''
        self.complete = False
        self.save()

    @staticmethod
    def _calc_sha256(data):
        hash = sha256()
        if hasattr(data, 'seek'):
            start = data.tell()
            while True:
                buf = data.read(1 << 20)
                if buf == '':
                    break
                hash.update(buf)
            data.seek(start)
        else:
            hash.update(data)
        return hash.hexdigest()
