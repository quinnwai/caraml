from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
import pandas as pd
from caraml.regressor.forms import FeaturesForm, UploadDatasetForm
from caraml.regressor.models import Dataset

def upload_file(request):
    if request.method == 'POST':
        form = UploadDatasetForm(request.POST, request.FILES)

        #TODO: check if csv before adding
        if form.is_valid():
            # make user the currently logged in user
            dataset = form.save(commit=False)
            dataset.user = request.user

            # save form with new changes
            dataset.save()
            form.save_m2m()

            # load in dataset and get relevant features (first column)
            data = pd.read_csv(dataset.file.path)
            request.session['allFeatures'] = list(data.columns)
            
            return HttpResponseRedirect('/feature') # TODO: change this to redirect to features page
    else:
        form = UploadDatasetForm()
    return render(request, 'regressor/upload-dataset.html', {'form': form})


class ChooseFeatures (FormView):
    template_name = 'pages/feature_form.html'
    form_class = FeaturesForm

    # overriding form_valid to provide redirect link
    def form_valid(self, form):
        df = form.save()
        df.save()
        return redirect('home')
