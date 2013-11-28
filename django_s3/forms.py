from django import forms

class UploadStartForm(forms.Form):
    blob = forms.IntegerField()


class UploadForm(forms.Form):
    blob = forms.IntegerField()
    token = forms.CharField()
    file = forms.FileField()
    resumableChunkNumber = forms.IntegerField()


class UploadFinishForm(forms.Form):
    blob = forms.IntegerField()
    token = forms.CharField()
