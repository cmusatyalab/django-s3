# Settings

## Required settings

If using the models, add `django_s3` to `INSTALLED_APPS`.

- `S3_HOST`: the hostname of the S3 endpoint
- `S3_ACCESS_KEY`: the access key ID
- `S3_SECRET_KEY`: the secret access key
- `S3_BUCKETS`: a `dict`.  Keys are abstract container names that can be
  passed to `Container.get()`.  Values are the corresponding bucket names.

## Optional settings

- `S3_STATICFILES_BUCKET`: the name of the bucket to be used by the
  `S3StaticFileStorage` and `S3CompressedFileStorage` classes
- `S3_PORT`: the port number of the S3 endpoint
- `S3_SECURE_CONN`: whether to use TLS *(default: True)*
- `S3_PUBLIC_HOST`: the hostname of a separate S3 endpoint to use in signed
  (public) URLs
- `S3_PUBLIC_PORT`: the port number of the public S3 endpoint
- `S3_PUBLIC_SECURE_CONN`: whether to use TLS for the public endpoint
  *(default: True)*
- `S3_SIGNED_URL_REFRESH_INTERVAL`: for signed URLs *not* provided for
  downloads (e.g. inline images), how often (in seconds) we should change
  the URL by default.  Objects will be cachable for half this time on
  average.  *(default: 8 hours)*
- `S3_SIGNED_URL_GRACE`: how long (in seconds) a signed URL should be valid
  by default after we are no longer handing it out.  This allows the user
  time to download the file.  *(default: 5 minutes)*
- `TEMPDIR`: a temporary directory for `manage.py validatestorage`.

# Storing static files in S3

If you're only using the static file support, you don't need to add
`django_s3` to `INSTALLED_APPS`.

```python
S3_STATICFILES_BUCKET = 'bucket-name'
STATIC_URL = 'https://storage.example.com/bucket-name/'
STATICFILES_STORAGE = 'django_s3.storage.S3StaticFileStorage'
```

## with django_compressor

```python
S3_STATICFILES_BUCKET = 'bucket-name'
STATIC_URL = 'https://storage.example.com/bucket-name/'
STATIC_ROOT = '/path/to/local/sitestatic'
STATICFILES_STORAGE = 'django_s3.storage.S3CompressedFileStorage'
COMPRESS_STORAGE = 'django_s3.storage.S3CompressedFileStorage'
```
