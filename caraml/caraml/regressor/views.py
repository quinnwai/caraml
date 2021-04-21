from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView

## calculation-specific imports
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
##

from caraml.regressor.forms import FeaturesForm, TargetForm, UploadDatasetForm, SpecificationsForm
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
            return HttpResponseRedirect('/feature')
    else:
        form = UploadDatasetForm()
    return render(request, 'regressor/upload-dataset.html', {'form': form})        

def ChooseFeaturesView(request):
    if request.method == 'POST':
        form = FeaturesForm(request, request.POST) 
        if form.is_valid():
            if not request.session.get('features'):
                request.session['features'] = []  # changing featureFormData to hold data from this submission
            request.session['features'] = form.cleaned_data['features']
            return redirect('/target') #TODO: Change redirect to the new form that you're gonna create
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
            return redirect('/specifications')
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
            return redirect('/results')  # TODO: Change redirect to the new form that you're gonna create
    else:
        form = SpecificationsForm(request=request)  # rendering form as usual from features
        return render(request, 'regressor/forms/specifications_form.html', {'form': form})

def ResultsView(request):
    # on page load
    if request.method == 'GET':

        # hardcoded examples (TODO: get rid after connecting to Vishal's work)
        # request.session['features'] = ["GDP per capita", "Social support", "Healthy life expectancy", "Freedom to make life choices",
                                    # "Generosity", "Perceptions of corruption"] # TODO: note exclusion of string variables for now
        # request.session['target'] = "Score"
        # request.session['title'] = "testing testing"
        # request.session['randomState'] = 4 # for reproducible output
        # request.session['numFolds'] = 10
        allFeatures = request.session["allFeatures"]
        features = []
        #append strings to list of features
        for i in request.session["features"]:
            features.append(allFeatures[int(i)])

        allTargets = request.session["allTargets"]
        #get target from location in allTargets
        target = allTargets[int(request.session["target"])]
        title = request.session["title"]
        randomState = request.session["randomState"]
        numFolds = request.session["numFolds"]

        # get specific dataset by name
        if(not title):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message
        
        dataset = Dataset.objects.get(title=request.session['title'])

        # ensure user inserted this dataset
        if(dataset.user != request.user):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        # check all variables are not null before proceeding

        if(not features and not target and not randomState and not numFolds):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        result = getResults(dataset.file.path, features, target, randomState, numFolds)
        
        return HttpResponse(f'average score of {result}')
        # return render(request, 'regressor/results.html')
    # return render(request, 'regressor/results.html') 
    # TODO: cover case of not get request?

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
