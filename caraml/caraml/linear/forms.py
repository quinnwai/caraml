
from caraml.linear.models import Dataset
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ModelForm, Form
from django.http import request

import copy

class UploadDatasetForm(ModelForm):
    class Meta:
        model = Dataset
        fields = ['title', 'file']

        labels = {
            'title': 'Title',
            'file': 'Dataset'
        }
    
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

class FeaturesForm(Form):

    def __init__(self, request, *args, **kwargs):
        super(FeaturesForm, self).__init__(*args, **kwargs)
        request.session["allFeatures"] = getFeatureOpts(request.session["allTargets"], request.session["target"])
        self.fields["features"] = forms.MultipleChoiceField(
            label="Features",
            choices=options(request.session["allFeatures"]),
            widget=forms.CheckboxSelectMultiple,
        )

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specify formatting
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

class TargetForm(Form):
    def __init__(self, request, *args, **kwargs):
        super(TargetForm, self).__init__(*args, **kwargs)
        #request.session["allTargets"] = options(request.session["allTargets"])
        self.fields["target"] = forms.ChoiceField(
            choices=options(request.session["allTargets"]),
            widget=forms.RadioSelect)

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specify formatting
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

class SpecificationsForm(Form):

    def __init__(self, request, *args, **kwargs):
        super(SpecificationsForm, self).__init__(*args, **kwargs)

        self.fields['trainTestSplit'] = forms.FloatField(
            label="Test Set Size (Proportion)",
            validators=[
                MinValueValidator(1e-6, message="Value must be greater than 0"),
                MaxValueValidator(1-1e-6, message="Value must be less than or equal to 1")
            ]
        )
        self.fields["randomState"] = forms.IntegerField(label="Random State")

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specify formatting
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))

def getFeatureOpts(allTargets, target):
    allFeatures = copy.deepcopy(allTargets)
    del allFeatures[int(target)]
    return allFeatures

def options(features):
    choices = []
    for i in range(len(features)):
        choices.append((i, features[i]))
    return choices
