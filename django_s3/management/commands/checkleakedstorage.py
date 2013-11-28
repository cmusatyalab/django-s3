from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from ...models import s3_conn, Blob

class Command(BaseCommand):
    args = '[--delete-blobs] [--delete-keys] [--delete-uploads]'
    help = 'Check for leaked storage, and optionally clean it up'
    option_list = BaseCommand.option_list + (
        make_option('--delete-blobs', action='store_true', default=False,
                help='Delete leaked Blob objects'),
        make_option('--delete-keys', action='store_true', default=False,
                help='Delete leaked S3 keys'),
        make_option('--delete-uploads', action='store_true', default=False,
                help='Delete leaked multipart uploads'),
    )

    def handle(self, delete_blobs, delete_keys, delete_uploads, **options):
        # Enumerate buckets
        buckets = [s3_conn.get_bucket(b) for b in settings.S3_BUCKETS.values()]

        # Check for leaked Blob objects
        leaked_blobs = 0
        for blob in Blob.objects.filter(artifact=None, derivedartifact=None):
            self.stdout.write('Leaked blob: %s\n' % blob)
            leaked_blobs += 1
            if delete_blobs:
                blob.delete()

        # Check for leaked bucket keys
        leaked_keys = 0
        for bucket in buckets:
            keys = set(Blob.objects.filter(container__name=bucket.name,
                    complete=True).values_list('name', flat=True))
            for key in bucket.list():
                if key.name not in keys:
                    self.stdout.write('Leaked key: %s\n' % key.name)
                    leaked_keys += 1
                    if delete_keys:
                        key.delete()

        # Check for leaked multipart uploads
        leaked_uploads = 0
        for bucket in buckets:
            upload_ids = set(Blob.objects.filter(container__name=bucket.name).
                    exclude(upload_id='').values_list('upload_id', flat=True))
            for upload in bucket.list_multipart_uploads():
                if upload.id not in upload_ids:
                    self.stdout.write('Leaked upload: %s\n' % upload.id)
                    leaked_uploads += 1
                    if delete_uploads:
                        upload.cancel_upload()

        # Summarize problems
        failed = False
        for type in 'blobs', 'keys', 'uploads':
            leaked = locals()['leaked_%s' % type]
            deleted = locals()['delete_%s' % type]
            if leaked:
                if deleted:
                    self.stdout.write('Deleted %d leaked %s\n' %
                            (leaked, type))
                else:
                    self.stdout.write('Found %d leaked %s\n' % (leaked, type))
                    failed = True
        if failed:
            raise CommandError('Found leaked objects')
