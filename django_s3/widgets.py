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
