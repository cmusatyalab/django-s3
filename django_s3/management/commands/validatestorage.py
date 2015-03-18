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

from django.core.management.base import NoArgsCommand, CommandError
from hashlib import sha256

from ...models import Blob

class Command(NoArgsCommand):
    help = 'Validate integrity of stored objects'

    def handle_noargs(self, verbosity=1, **options):
        failed = 0
        for blob in Blob.objects.all():
            if not blob.complete:
                continue
            if int(verbosity) > 1:
                self.stderr.write('Checking: %s\n' % blob)

            key = blob.get()
            try:
                hash = sha256()
                while True:
                    buf = key.read(1 << 20)
                    if not buf: break
                    hash.update(buf)
                found = hash.hexdigest()
            except Exception:
                key.close(fast=True)
                raise
            else:
                key.close()

            if not blob.sha256:
                self.stdout.write('Replacing missing checksum: %s\n' % blob)
                blob.sha256 = found
                blob.save()

            elif blob.sha256 != found:
                self.stdout.write('Integrity check failed: %s\n' % blob)
                self.stdout.write('  Expected : %s\n' % blob.sha256)
                self.stdout.write('  Found    : %s\n' % found)
                failed += 1

        if failed:
            raise CommandError('%d objects failed validation' % failed)
