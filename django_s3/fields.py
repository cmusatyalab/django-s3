#
# Copyright (C) 2012 Carnegie Mellon University
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
