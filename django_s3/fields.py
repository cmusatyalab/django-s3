from django import forms

from .widgets import *

class BlobAdminField(forms.Field):
    # Field providing UI for uploading a file.  The output of the field
    # should be ignored.  The form constructor must set our initial value to
    # the PK of the Blob to upload, or None.

    def __init__(self, required=False, widget=BlobAdminWidget, label='Data',
            initial=None, help_text=None):
        # The output value is meaningless, so override required
        super(BlobAdminField, self).__init__(required=False,
                widget=widget, label=label, initial=initial,
                help_text=help_text)

    def bound_data(self, data, initial):
        # Ensure that bound and unbound forms have the same field value
        return initial

    def clean(self, value):
        # Can't change the value
        return self.initial
