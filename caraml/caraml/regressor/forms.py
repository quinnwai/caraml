from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import ModelForm
from django.http import request
from caraml.regressor.models import Dataset
import copy

class UploadDatasetForm(ModelForm):
    class Meta:
        model = Dataset
        fields = ['title', 'file']
    
    def __init__(self, *args, **kwargs):
        super(UploadDatasetForm, self).__init__(*args, **kwargs)

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self) 

        # specifying FORMatting... hah fun times
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

class FeaturesForm(forms.Form):

    def __init__(self, request, *args, **kwargs):
        super(FeaturesForm, self).__init__(*args, **kwargs)
        self.fields["features"] = forms.MultipleChoiceField(
        choices=options(request.session["allFeatures"]),
        widget=forms.CheckboxSelectMultiple,)

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specifying FORMatting... hah fun times
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

class TargetForm(forms.Form):

    def __init__(self, request, *args, **kwargs):
        super(TargetForm, self).__init__(*args, **kwargs)
        request.session["allTargets"] = getTargetOpts(request.session["allFeatures"],
                          request.session["features"])
        self.fields["target"] = forms.ChoiceField(
            choices=options(request.session["allTargets"]),
            widget=forms.RadioSelect,)

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specifying FORMatting... hah fun times
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

class FeaturesForm(forms.Form):

    def __init__(self, request, *args, **kwargs):
        super(FeaturesForm, self).__init__(*args, **kwargs)
        self.fields["features"] = forms.MultipleChoiceField(
        choices=options(request.session["allFeatures"]),
        widget=forms.CheckboxSelectMultiple,)

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specifying FORMatting... hah fun times
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

class SpecificationsForm(forms.Form):

    def __init__(self, request, *args, **kwargs):
        super(SpecificationsForm, self).__init__(*args, **kwargs)
        self.fields["randomState"] = forms.IntegerField()
        self.fields["nFolds"] = forms.IntegerField()

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specifying FORMatting... hah fun times
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

def getTargetOpts(allFeatures, features):
    allTargets = copy.deepcopy(allFeatures)
    for i in reversed(features):
        del allTargets[int(i)]
    return allTargets

def options(features):
    choices = []
    for i in range(len(features)):
        choices.append((i, features[i]))
    return choices
