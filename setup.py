from distutils.core import setup

setup(
    name = 'django-s3',
    packages = [
        'django_s3',
        'django_s3.management',
        'django_s3.management.commands',
        'django_s3.migrations',
    ],
    package_data = {
        'django_s3': [
            'static/css/*.css',
            'static/js/*.js',
            'static/js/libs/*.js',
        ],
    },
    description = 'Amazon S3 storage for Django',
    license = 'GNU General Public License, version 2',
)
