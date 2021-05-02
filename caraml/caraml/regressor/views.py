from csv import reader
from django.conf import settings
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from pickle import dump, load
from . models import Record, Dataset
import os
import csv


## calculation-specific imports
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder

## graph-specific imports/settings
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

from caraml.users.views import User
from caraml.regressor.forms import FeaturesForm, TargetForm, UploadDatasetForm, SpecificationsForm

class RecordsListView(ListView):
    template_name = 'users/records.html'

    def get_queryset(self):
        RecordsList = Record.objects.all().filter(user = self.request.user).order_by('-dateTime')
        return RecordsList

    def get_context_data(self, **kwargs):
        context = super(RecordsListView, self).get_context_data(**kwargs)
        print(context)
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

                # get rid of all session variables
            keys = list(request.session.keys())
            for key in keys:
                if key[0] != '_':
                    del request.session[key]

            # load in dataset and store all features and dataset title into the session
            data = pd.read_csv(dataset.file.path)
            request.session['title'] = dataset.title
            request.session['allTargets'] = list(data.columns)
            return HttpResponseRedirect('/target')
    else:
        form = UploadDatasetForm()
    return render(request, 'regressor/upload-dataset.html', {'form': form})   


def SecondUploadView(request):
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
            return HttpResponseRedirect('/prediction')
    else:
        form = UploadDatasetForm()
    return render(request, 'regressor/second-upload.html', {'form': form})

def FeatureVisualizationView(request):
    # on page load
    if request.method == 'GET':
        # get scatter plot images
        image_paths = scatterplotFeatures(request)

        # store name of target
        target_idx = request.session["target"]
        target = request.session["allTargets"][target_idx]

        # store imagePaths to be deleted later
        request.session["imagePaths"] = image_paths

        # prepare variables before loading template
        context = {'image_paths': image_paths, 'target': target}
        return render(request, 'regressor/feature-visualization.html', context)
    return render(request, 'regressor/feature-visualization.html')

class ChooseFeaturesView(FormView):
    template_name = 'regressor/forms/feature_form.html'
    form_class = FeaturesForm
    success_url = '/specifications'

    # sets up request to use
    # Source: https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    def get_form_kwargs(self):
        kwargs = super(ChooseFeaturesView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        if not self.request.session.get('features'):
            self.request.session['features'] = []  # changing featureFormData to hold data from this submission
            self.request.session['features'] = form.cleaned_data['features']
            return HttpResponseRedirect('/specifications')

class ChooseTargetView(FormView):
    template_name = 'regressor/forms/target_form.html'
    form_class = TargetForm
    success_url = '/visualization'

    # sets up request to use
    # Source: https://chriskief.com/2012/12/18/django-modelform-formview-and-the-request-object/
    def get_form_kwargs(self):
        kwargs = super(ChooseTargetView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if not self.request.session.get('target'):
                self.request.session['target'] = []  # changing featureFormData to hold data from this submission
        self.request.session['target'] = int(form.cleaned_data['target'])
        return HttpResponseRedirect('/visualization')


def ChooseSpecificationsView(request):
    if request.method == 'POST':
        form = SpecificationsForm(request, request.POST)
        if form.is_valid():
            if not request.session.get('specifications'):
                request.session['specifications'] = []  # changing featureFormData to hold data from this submission
            request.session['randomState'] = form.cleaned_data['randomState']
            request.session['numFolds'] = form.cleaned_data['nFolds']
            return HttpResponseRedirect('/results') 
    else:
        form = SpecificationsForm(request=request)  # rendering form as usual from features
        return render(request, 'regressor/forms/specifications_form.html', {'form': form})

def ResultsView(request):
    # on page load
    if request.method == 'GET':

        # get all possible feature and targets from session
        allFeatures = request.session.get("allFeatures", None)
        allTargets = request.session.get("allTargets", None)
        features = []

        # append strings to list of features
        for i in request.session["features"]:
            features.append(allFeatures[int(i)])

        # get target from location in allTargets
        if allTargets and request.session.get("target", None):
            target = allTargets[int(request.session.get("target", None))]
        title = request.session.get("title", None)
        randomState = request.session.get("randomState", None)
        numFolds = request.session.get("numFolds", None)

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


        # TODO: delete all images
        # imagePaths = request.session["imagePaths"]
        # for imagePath in imagePaths:
        #     # if(os.path.relpathexists(imagePath)):
        #         # print("path exists \n\n")
        #         # os.remove(imagePath)
        #     os.remove(imagePath)

        # prepare variables and return them with template
        context = { 'result': round(result*100, 2) }
        return render(request, 'regressor/results.html', context)

def getResults(filePath, features, target, randomState, numFolds):
    ##### data preprocessing #####
    # create pandas dataframe
    data = pd.read_csv(filePath)

    # create feature dataset and labels
    X = data.loc[:,features]
    y = data.loc[:,target]
    
    # add indices of features that are strings
    str_indices = []
    for i in range(0, len(features)):
        if(isinstance(X.loc[0, features[i]], str)):
            str_indices.append(i)

    # if strings columns exist, split dataset into numeric and string data
    if (len(str_indices) != 0):
        # separate X into numeric and non-numerical (string-based) datasets using feature labels
        features = np.array(features)
        str_features = features[str_indices]
        X_str = X[str_features]
        X_num = X.drop(str_features, axis=1)

        # fit One Hot Encoder model
        enc = OneHotEncoder().fit(X_str)

        # for each category of arrays, create column labels for dataframe later
        for i in range(len(enc.categories_)):
            if(i == 0):
                columns = enc.categories_[i]
            else:
                columns = np.concatenate((columns, enc.categories_[i]))
        
        # create encoded array and join with numerical array
        X_enc = pd.DataFrame(enc.transform(X_str).toarray(), columns=columns)
        X = pd.concat([X_num, X_enc], axis=1)

    # initialize KFolds
    kf = KFold(n_splits=numFolds, shuffle=True, random_state=randomState)

    # set score to be averaged returned later
    score = 0

    ##### cross validation and model evaluation #####
    for fold, (train_idx, test_idx) in enumerate(kf.split(X)):
        ## pre-processing phase
        #define training and test datasets
        X_train = X.loc[train_idx,:]
        X_test = X.loc[test_idx,:]
        y_train = y.loc[train_idx]
        y_test = y.loc[test_idx]

        ## use linear regression to predict and get r squared
        # create and fit model
        model = LinearRegression().fit(X_train, y_train)

        # predict using new model and compute r_squared value
        dump(model, open('model.pkl', 'wb'))
        r_squared = model.score(X_test, y_test)

        # sum
        score += r_squared

    avg_score = score/(fold+1)

    return avg_score

def getPredictions(filePath, features):
    
    data = pd.read_csv(filePath)
    X = data.loc[:, features]
    # add indices of features that are strings
    str_indices = []
    for i in range(0, len(features)):
        if(isinstance(X.loc[0, features[i]], str)):
            str_indices.append(i)

    # if strings columns exist, split dataset into numeric and string data
    if (len(str_indices) != 0):
        # separate X into numeric and non-numerical (string-based) datasets using feature labels
        features = np.array(features)
        str_features = features[str_indices]
        X_str = X[str_features]
        X_num = X.drop(str_features, axis=1)

        # fit One Hot Encoder model
        enc = OneHotEncoder().fit(X_str)

        # for each category of arrays, create column labels for dataframe later
        for i in range(len(enc.categories_)):
            if(i == 0):
                columns = enc.categories_[i]
            else:
                columns = np.concatenate((columns, enc.categories_[i]))

        # create encoded array and join with numerical array
        X_enc = pd.DataFrame(enc.transform(X_str).toarray(), columns=columns)
        X = pd.concat([X_num, X_enc], axis=1)
    X_new = X.loc[:]
    model = load(open('model.pkl', 'rb'))
    y_pred = model.predict(X_new)
    return y_pred

def PredictionsView(request):
    # Open the input_file in read mode and output_file in write mode
    title = request.session["title"]
    allFeatures = request.session.get("allFeatures", None)
    features = []

    # append strings to list of features
    for i in request.session["features"]:
        features.append(allFeatures[int(i)])
    if(not title):
        # TODO: return to previous page with message
        return HttpResponse("Invalid page access. Please return to a different page")

    dataset = Dataset.objects.get(title=request.session['title'])
    filePath = dataset.file.path

    # ensure user inserted this dataset
    if(dataset.user != request.user):
        # TODO: return to previous page with message
        return HttpResponse("Invalid page access. Please return to a different page")

    # check all variables are not null before proceeding

    if(not features):
        # TODO: return to previous page with message
        return HttpResponse("Invalid page access. Please return to a different page")
    y_pred = getPredictions(filePath, features)
    response = HttpResponse(content_type='text/csv')
    
    # print(filePath)
    csv_input = pd.read_csv(filePath)
    csv_input['Predictions'] = y_pred
    csv_input.to_csv(response, index=False)

    # delete dataset file and instance
    if(os.path.exists(filePath)):
        os.remove(filePath)
    dataset.delete()
    response['Content-Disposition'] = 'attachment; filename="predictions.csv"'
    return response

# plots all scatter plots and stores them as images. Returns list of image paths
def scatterplotFeatures(request):
    # Source: https://projectsplaza.com/how-to-create-bar-chart-image-with-matplotlib-in-django/

    # variable to return
    image_paths = []

    # get all features, target, and dataset by name
    allTargets = request.session.get('allTargets', None)
    target = request.session.get('target', None)

    title = request.session.get('title', None)
    if(not title):
        return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to upload csv page with message
    dataset = Dataset.objects.get(title=title)
    path = dataset.file.path
    data = pd.read_csv(path)

    # get features and index into y
    y = data.iloc[:,target]
    y_lbl = allTargets[target]

    # for each feature, plot the function (must be int)
    for i in range(len(allTargets)):
        # store all relevant info
        feature = allTargets[i]
        X = data.iloc[:,i]

        # check if numerical
        if (np.issubdtype(X.dtype, np.integer) or np.issubdtype(X.dtype, np.floating)) and i != target:
            plt.scatter(X, y, color="darkgoldenrod")
            plt.title(f'{y_lbl} vs {feature}')
            plt.xlabel(feature)
            plt.ylabel(y_lbl)
            
            # add path to return list and save figure to path
            image_path = f'graphs/{request.user.username}{i}.png'
            image_paths.append(f'../media/{image_path}')

            plt.savefig(f'{settings.MEDIA_ROOT}/{image_path}')
            plt.clf()
    
    return image_paths
