from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from itertools import chain
from tempfile import TemporaryFile

from ...models import Artifact, DerivedArtifact, DataCorruption

class Command(NoArgsCommand):
    help = 'Validate integrity of stored objects'

    def handle_noargs(self, verbosity=1, **options):
        failed = 0
        for obj in chain(Artifact.objects.all(),
                DerivedArtifact.objects.all()):
            if not obj.blob.complete:
                continue
            if int(verbosity) > 1:
                self.stderr.write('Checking: %s\n' % obj)
            with TemporaryFile(dir=getattr(settings, 'TEMPDIR', None),
                    prefix='olive-blob-') as fh:
                obj.blob.get(fh)
                fh.seek(0)
                try:
                    obj.blob.check_sha256(fh)
                except ValueError:
                    # SHA-256 not set; set it
                    obj.blob.set_sha256(fh)
                except DataCorruption, e:
                    self.stdout.write('Integrity check failed: %s\n' % obj)
                    self.stdout.write('  Expected : %s\n' % e.expected)
                    self.stdout.write('  Found    : %s\n' % e.found)
                    failed += 1
        if failed:
            raise CommandError('%d objects failed validation' % failed)
