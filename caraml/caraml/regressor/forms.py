from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import ModelForm
from caraml.regressor.models import Dataset

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


features = ["car", "train", "plane", "universe", "time"]
choices = []
for i in range(len(features)):
    choices.append((i, features[i]))

class FeaturesForm(forms.Form):
    choose = forms.MultipleChoiceField(choices=choices, 
    widget=forms.CheckboxSelectMultiple,)
    your_name = forms.CharField(label='Your name', max_length=100)

    def __init__(self, *args, **kwargs):
        super(FeaturesForm, self).__init__(*args, **kwargs)

        # defined so that crispy forms front-end is simple
        self.helper = FormHelper(self)

        # specifying FORMatting... hah fun times
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Submit'))