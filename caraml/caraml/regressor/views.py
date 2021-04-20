from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView

## calculation-specific imports
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
##

from caraml.regressor.forms import FeaturesForm, UploadDatasetForm
from caraml.regressor.models import Dataset

def UploadDatasetView(request):
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

            # load in dataset and store all features and dataset title into the session
            data = pd.read_csv(dataset.file.path)
            request.session['title'] = dataset.title
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

def ResultsView(request):
    # on page load
    if request.method == 'GET':

        # hardcoded examples (TODO: get rid after connecting to Vishal's work)
        request.session['features'] = ["GDP per capita", "Social support", "Healthy life expectancy", "Freedom to make life choices",
                                    "Generosity", "Perceptions of corruption"] # TODO: note exclusion of string variables for now
        request.session['target'] = "Score"
        request.session['title'] = "testing testing"
        request.session['testSize'] = 0.8
        request.session['randomState'] = 4 # for reproducible output
        request.session['numFolds'] = 10

        # get all variables needed
        features = request.session.get('features', None)
        target = request.session.get('target', None) # assuming sent as target 
        title = request.session.get('title', None)
        testSize = request.session.get('testSize', None)
        randomState = request.session.get('randomState', None)
        numFolds = request.session.get('numFolds', None)



        # get specific dataset by name
        if(not title):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message
        
        dataset = Dataset.objects.get(title=request.session['title'])

        # ensure user inserted this dataset
        if(dataset.user != request.user):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        # check all variables are not null before proceeding

        if(not features and not target and not testSize and not randomState and not numFolds):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        result = getResults(dataset.file.path, features, target, testSize, randomState, numFolds)
        
        return HttpResponse(f'average score of {result}')
        # return render(request, 'regressor/results.html')
    # return render(request, 'regressor/results.html') 
    # TODO: cover case of not get request?

def getResults(filePath, features, target, testSize, randomState, numFolds):
    ##### data preprocessing #####
    # create pandas dataframe
    data = pd.read_csv(filePath)

    X = data.loc[:,features]
    y = data.loc[:,target]

    # initialize KFolds
    kf = KFold(n_splits=numFolds, shuffle=True, random_state=randomState)

    # set score to be averaged returned later
    score = 0

    ##### cross validation and model evaluation #####
    for fold, (train_idx, test_idx) in enumerate(kf.split(X)):
        ## pre-processing phase
        #define train and test 
        X_train = X.loc[train_idx,:]
        X_test = X.loc[test_idx,:]
        y_train = y.loc[train_idx]
        y_test = y.loc[test_idx]

        ## use k-NN to predict and get r squared
        # create and fit model
        model = LinearRegression().fit(X_train, y_train)

        # predict using new model and compute r_squared value
        y_pred = model.predict(X_test)
        r_squared = model.score(X_test, y_test)

        # sum
        score += r_squared

    avg_score = score/(fold+1)

    return avg_score