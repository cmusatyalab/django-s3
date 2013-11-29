from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from tempfile import TemporaryFile

from ...models import Blob, DataCorruption

class Command(NoArgsCommand):
    help = 'Validate integrity of stored objects'

    def handle_noargs(self, verbosity=1, **options):
        failed = 0
        for blob in Blob.objects.all():
            if not blob.complete:
                continue
            if int(verbosity) > 1:
                self.stderr.write('Checking: %s\n' % blob)
            with TemporaryFile(dir=getattr(settings, 'TEMPDIR', None),
                    prefix='olive-blob-') as fh:
                blob.get(fh)
                fh.seek(0)
                try:
                    blob.check_sha256(fh)
                except ValueError:
                    # SHA-256 not set; set it
                    blob.set_sha256(fh)
                except DataCorruption, e:
                    self.stdout.write('Integrity check failed: %s\n' % blob)
                    self.stdout.write('  Expected : %s\n' % e.expected)
                    self.stdout.write('  Found    : %s\n' % e.found)
                    failed += 1
        if failed:
            raise CommandError('%d objects failed validation' % failed)
