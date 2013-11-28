from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import filesizeformat
from django.views.decorators.http import require_POST
from functools import wraps
import json

from .forms import *
from .models import *
from .signals import upload_complete

def _upload_view(form_class):
    def decorator(f):
        @require_POST
        @permission_required('django_s3.change_blob')
        @wraps(f)
        def wrapper(request):
            # Return 500 when we mean 400, because resumable.js thinks 400
            # means "retry"
            form = form_class(request.POST, request.FILES)
            if not form.is_valid():
                return HttpResponseServerError('Invalid form')
            blob = get_object_or_404(Blob.objects,
                    id=form.cleaned_data['blob'])
            if blob.complete:
                return HttpResponseServerError('Blob already complete')
            if ('token' in form.cleaned_data and
                    form.cleaned_data['token'] != blob.upload_id):
                return HttpResponseServerError('Upload session terminated')
            return f(request, form, blob)
        return wrapper
    return decorator

@_upload_view(UploadStartForm)
def upload_start(request, form, blob):
    blob.start_segments()
    return HttpResponse(json.dumps({
        'token': blob.upload_id,
    }), mimetype='application/json')

@_upload_view(UploadForm)
def upload_chunk(request, form, blob):
    blob.put_segment(form.cleaned_data['resumableChunkNumber'],
            form.cleaned_data['file'])
    # Should be 204, but resumable.js wants 200
    return HttpResponse()

@_upload_view(UploadFinishForm)
def upload_finish(request, form, blob):
    blob.commit_segments()
    upload_complete.send(sender=upload_finish, request=request, blob=blob)
    return HttpResponse(json.dumps({
        'size': filesizeformat(blob.size),
    }), mimetype='application/json')
