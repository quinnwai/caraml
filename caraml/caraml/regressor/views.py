from caraml.regressor.forms import FeaturesForm
from django.shortcuts import render
from django.views.generic.edit import FormView

# Create your views here.


class ChooseFeatures (FormView):
    template_name = 'pages/feature_form.html'
    form_class = FeaturesForm

    # overriding form_valid to provide redirect link
    def form_valid(self, form):
        df = form.save()
        df.save()
        return redirect('home')
