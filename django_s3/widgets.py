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

from django import forms
from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat
from django.utils.html import mark_safe

from .models import Blob

class BlobAdminWidget(forms.Widget):
    class Media:
        css = {
            'all': (
                'css/blobadmin.css',
            )
        }
        js = (
            'js/libs/resumable.js',
            'js/blobadmin.js',
        )

    def render(self, name, value, attrs=None):
        def output(data, notice=False):
            if notice:
                data = '<div class="upload-notice">%s</div>' % data
            return mark_safe(unicode(data))

        if value is None:
            return output('Save form first', True)

        try:
            blob = Blob.objects.get(id=value)
        except Blob.DoesNotExist:
            return output('Not found', True)

        if blob.complete:
            if blob.size is None:
                return output('unknown KB')
            else:
                return output(filesizeformat(blob.size))

        html = ('<span class="upload-field" data-blob="%(blob)d"' +
                'data-upload-start="%(start)s" data-upload-chunk="%(chunk)s"' +
                'data-upload-finish="%(finish)s"></span>')
        args = {
            'blob': blob.id,
            'start': reverse('s3-upload-start'),
            'chunk': reverse('s3-upload-chunk'),
            'finish': reverse('s3-upload-finish'),
        }
        return output(html % args)
