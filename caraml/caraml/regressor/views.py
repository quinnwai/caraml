from caraml.users.views import User
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from . models import Record, Dataset
import os

## calculation-specific imports
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
##

from caraml.regressor.forms import FeaturesForm, TargetForm, UploadDatasetForm, SpecificationsForm

class RecordsListView(ListView):
    template_name = 'users/records.html'

    def get_queryset(self):
        RecordsList = Record.objects.all().filter(user = self.request.user)
        return RecordsList

    def get_context_data(self, **kwargs):
        context = super(RecordsListView, self).get_context_data(**kwargs)
        return context

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
            request.session['allTargets'] = list(data.columns)
            return HttpResponseRedirect('/target')
    else:
        form = UploadDatasetForm()
    return render(request, 'regressor/upload-dataset.html', {'form': form})   

def FeatureVisualizationView(request):
    return render(request, 'regressor/feature-visualization.html')

def ChooseFeaturesView(request):
    if request.method == 'POST':
        form = FeaturesForm(request, request.POST) 
        if form.is_valid():
            if not request.session.get('features'):
                request.session['features'] = []  # changing featureFormData to hold data from this submission
            request.session['features'] = form.cleaned_data['features']
            return HttpResponseRedirect('/specifications') #TODO: Change redirect to the new form that you're gonna create
    else:
        form = FeaturesForm(request=request)  # rendering form as usual from features
        return render(request, 'regressor/forms/feature_form.html', {'form': form})


def ChooseTargetView(request):
    if request.method == 'POST':
        form = TargetForm(request, request.POST)
        if form.is_valid():
            if not request.session.get('target'):
                request.session['target'] = []  # changing featureFormData to hold data from this submission
            request.session['target'] = form.cleaned_data['target']
            return HttpResponseRedirect('/visualization')
    else:
        form = TargetForm(request=request)  # rendering form as usual from features
        return render(request, 'regressor/forms/target_form.html', {'form': form})


def ChooseSpecificationsView(request):
    if request.method == 'POST':
        form = SpecificationsForm(request, request.POST)
        if form.is_valid():
            if not request.session.get('specifications'):
                request.session['specifications'] = []  # changing featureFormData to hold data from this submission
            request.session['randomState'] = form.cleaned_data['randomState']
            request.session['numFolds'] = form.cleaned_data['nFolds']
            return HttpResponseRedirect('/results')  # TODO: Change redirect to the new form that you're gonna create
    else:
        form = SpecificationsForm(request=request)  # rendering form as usual from features
        return render(request, 'regressor/forms/specifications_form.html', {'form': form})

def ResultsView(request):
    # on page load
    if request.method == 'GET':

        # get all possible feature and targets from session
        allFeatures = request.session["allFeatures"]
        allTargets = request.session["allTargets"]
        features = []

        # append strings to list of features
        for i in request.session["features"]:
            features.append(allFeatures[int(i)])

        # get target from location in allTargets
        target = allTargets[int(request.session["target"])]
        title = request.session["title"]
        randomState = request.session["randomState"]
        numFolds = request.session["numFolds"]

        # get specific dataset by name
        if(not title):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message
        
        dataset = Dataset.objects.get(title=request.session['title'])
        path = dataset.file.path

        # ensure user inserted this dataset
        if(dataset.user != request.user):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        # check all variables are not null before proceeding

        if(not features and not target and not randomState and not numFolds):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        # get result to print out (training and testing)
        result = getResults(path, features, target, randomState, numFolds)

        # create new Record object from parameters
        Record.objects.create(
            title=title,
            user=request.user,
            randomState=randomState,
            numFolds=numFolds,
            target=target,
            features = features,
            result=(result*100))

        # delete dataset file and instance
        if(os.path.exists(path)):
            os.remove(path)
        dataset.delete()

        # get rid of all session variables
        keys = list(request.session.keys())
        for key in keys:
            if key[0]!='_':
                del request.session[key]

        context = {
        'result': round(result*100, 2)
        }
        
        # return HttpResponse(f'average score of {result}')
        return render(request, 'regressor/results.html', context)

def getResults(filePath, features, target, randomState, numFolds):
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
