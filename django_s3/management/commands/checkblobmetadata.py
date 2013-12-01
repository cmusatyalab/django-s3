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

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from ...models import Blob

class Command(BaseCommand):
    help = 'Check blob Content-Types and sizes against database'
    args = '[--fix-types] [--clobber-sizes]'
    option_list = BaseCommand.option_list + (
        make_option('--fix-types', action='store_true', default=False,
                help='Update S3 Content-Types from database'),
        make_option('--clobber-sizes', action='store_true', default=False,
                help='Update database Blob sizes from S3 (USE CAUTION)'),
    )

    def handle(self, fix_types, clobber_sizes, **options):
        failed = 0
        for blob in Blob.objects.filter(complete=True).order_by(
                'container__name', 'name'):
            # Force a HEAD request
            key = blob.container.bucket.get_key(blob.name)
            ok = True
            if blob.size != key.size:
                self.stdout.write('%s: Database length %d, S3 length %d\n' % (
                        blob, blob.size, key.size))
                if clobber_sizes:
                    blob.size = key.size
                    blob.save()
                else:
                    ok = False
            if blob.content_type != key.content_type:
                self.stdout.write('%s: Database type %s, S3 type %s\n' % (
                        blob, blob.content_type, key.content_type))
                if fix_types:
                    blob.key.copy(blob.container.name, blob.name,
                            metadata={'Content-Type': str(blob.content_type)},
                            preserve_acl=True)
                else:
                    ok = False
            if not ok:
                failed += 1
        if failed:
            raise CommandError('%d Blobs failed validation' % failed)
