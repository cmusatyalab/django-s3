from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns('',
    url(r'^$', upload_chunk, name='s3-upload-chunk'),
    url(r'start/$', upload_start, name='s3-upload-start'),
    url(r'finish/$', upload_finish, name='s3-upload-finish'),
)
