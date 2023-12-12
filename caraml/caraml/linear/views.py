from csv import reader
from django.conf import settings
from django.contrib.sessions.models import Session
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
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import OneHotEncoder

## graph-specific imports/settings
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

from caraml.users.views import User
from caraml.linear.forms import FeaturesForm, TargetForm, UploadDatasetForm, SpecificationsForm

class RecordsListView(ListView):
    template_name = 'users/records.html'

    def get_queryset(self):
        RecordsList = Record.objects.all().filter(user = self.request.user).order_by('-dateTime')
        return RecordsList

    def get_context_data(self, **kwargs):
        context = super(RecordsListView, self).get_context_data(**kwargs)
        return context

def UploadDatasetView(request):
    if request.method == 'POST':
        form = UploadDatasetForm(request.POST, request.FILES)

        if form.is_valid():
            # make dataset's author the current user
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
                
            # # TODO: replace above with this
            # sessions = Session.objects.filter(session_key=request.session.session_key)
            # for session in sessions:
            #     session_data = session.get_decoded()
            #     session_data.clear()
            #     session.save()

            # load in dataset and ensure dataset is readable
            path = dataset.file.path
            try:
                data = pd.read_csv(path)
            except:
                if os.path.exists(path):
                    os.remove(path)
                dataset.delete()
                return HttpResponseRedirect('/upload-dataset')

            #  store all features and dataset title into the session
            request.session['title'] = dataset.title
            request.session['allTargets'] = list(data.columns)
            return HttpResponseRedirect('/specifications')
    else:
        form = UploadDatasetForm()
    return render(request, 'linear/upload-dataset.html', {'form': form})   

        
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
    return render(request, 'linear/second-upload.html', {'form': form})

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
        image_paths = ["../media/" + path for path in image_paths]
        context = {'image_paths': image_paths, 'target': target}

        return render(request, 'linear/feature-visualization.html', context)
    return render(request, 'linear/feature-visualization.html')

class ChooseFeaturesView(FormView):
    template_name = 'linear/forms/feature_form.html'
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
            return HttpResponseRedirect('/results')

class ChooseTargetView(FormView):
    template_name = 'linear/forms/target_form.html'
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
            request.session['trainTestSplit'] = form.cleaned_data['trainTestSplit']
            request.session['randomState'] = form.cleaned_data['randomState']
            return HttpResponseRedirect('/target') 
    else:
        form = SpecificationsForm(request=request)  # rendering form as usual from features
        return render(request, 'linear/forms/specifications_form.html', {'form': form})

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
        if allTargets and request.session.get("target", None) is not None:
            target = allTargets[int(request.session.get("target", None))]
        title = request.session.get("title", None)
        randomState = request.session.get("randomState", None)
        trainTestSplit = request.session.get("trainTestSplit", None)

        # get specific dataset by name
        if not title:
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message
        
        dataset = Dataset.objects.get(title=request.session['title'])
        path = dataset.file.path

        # ensure user inserted this dataset
        if dataset.user != request.user:
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        # check all variables are not null before proceeding
        if not (features and target and randomState and trainTestSplit):
            return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to previous page with message

        # get result to print out (training and testing)
        train_error, test_error = getResults(
                path, trainTestSplit, features, target, randomState)

        # create new Record object from parameters
        Record.objects.create(
            title=title,
            user=request.user,
            randomState=randomState,
            target=target,
            features=features,
            trainError=train_error,
            testError=test_error)

        # delete dataset file and instance
        print(f"file loc: {path}")
        if os.path.exists(path):
            print("deleting dataset")
            os.remove(path)
        dataset.delete()


        # delete all images
        imagePaths = request.session["imagePaths"]
        for imagePath in imagePaths:
            newPath = f'{settings.MEDIA_ROOT}/{imagePath}'

            if os.path.exists(newPath):
                os.remove(newPath)

        # prepare variables and return them with template
        context = { 
            'train_error': round(train_error, 4),
            'test_error': round(test_error, 4)
        }

        return render(request, 'linear/results.html', context)

def getResults(filePath, testSplit, features, target, randomState):
    ##### data preprocessing #####
    # create pandas dataframe
    data = pd.read_csv(filePath)

    # create dataset for features and labels according to user
    X = data.loc[:,features]
    y = data.loc[:,target]
    
    # add indices of features that are strings
    str_indices = []
    for i in range(0, len(features)):
        if isinstance(X.loc[0, features[i]], str):
            print(features[i])
            str_indices.append(i)

    # if strings columns exist, one hot encode the dataset
    if len(str_indices) != 0:
        # separate X into numeric and non-numerical (string-based) datasets using feature labels
        features = np.array(features)
        str_features = features[str_indices]
        X_str = X[str_features]
        X.drop(str_features, axis=1, inplace=True)

        # fit One Hot Encoder model
        enc = OneHotEncoder().fit(X_str)

        # for each category of arrays, create column labels for dataframe later
        for i in range(len(enc.categories_)):
            if i == 0:
                columns = enc.categories_[i]
            else:
                columns = np.concatenate((columns, enc.categories_[i]))
        
        # add one-hot encoded columns
        X[columns] = enc.transform(X_str).toarray()

    # split into test and train data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=testSplit, random_state=randomState)

    model = LinearRegression().fit(X_train, y_train)
    train_error = model.score(X_train, y_train)
    test_error = model.score(X_test, y_test)

    return train_error, test_error

def getPredictions(filePath, features):
    
    data = pd.read_csv(filePath)
    X = data.loc[:, features]
    # add indices of features that are strings
    str_indices = []
    for i in range(0, len(features)):
        if isinstance(X.loc[0, features[i]], str):
            str_indices.append(i)

    # if strings columns exist, split dataset into numeric and string data
    if len(str_indices) != 0:
        # separate X into numeric and non-numerical (string-based) datasets using feature labels
        features = np.array(features)
        str_features = features[str_indices]
        X_str = X[str_features]
        X_num = X.drop(str_features, axis=1)

        # fit One Hot Encoder model
        enc = OneHotEncoder().fit(X_str)

        # for each category of arrays, create column labels for dataframe later
        for i in range(len(enc.categories_)):
            if i == 0:
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
    if not title:
        # TODO: return to previous page with message
        return HttpResponse("Invalid page access. Please return to a different page")

    dataset = Dataset.objects.get(title=request.session['title'])
    filePath = dataset.file.path

    # ensure user inserted this dataset
    if dataset.user != request.user:
        # TODO: return to previous page with message
        return HttpResponse("Invalid page access. Please return to a different page")

    # check all variables are not null before proceeding

    if not features:
        # TODO: return to previous page with message
        return HttpResponse("Invalid page access. Please return to a different page")
    y_pred = getPredictions(filePath, features)
    response = HttpResponse(content_type='text/csv')
    
    csv_input = pd.read_csv(filePath)
    csv_input['Predictions'] = y_pred
    csv_input.to_csv(response, index=False)

    # delete dataset file and instance
    if os.path.exists(filePath):
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
    if not title:
        return HttpResponse("Invalid page access. Please return to a different page") # TODO: return to upload csv page with message
    dataset = Dataset.objects.get(title=title)
    path = dataset.file.path
    data = pd.read_csv(path)
    
    

    # get features and index into y
    y = data.iloc[:,target]
    y_lbl = allTargets[target]

    # for each feature, plot a target vs feature scatterplot
    for i in range(len(allTargets)):
        # get feature and data column from index
        feature = allTargets[i]
        X = data.iloc[:,i]
        X_train, _, y_train, _ = train_test_split(X, y,
            test_size=request.session['trainTestSplit'], random_state=request.session['randomState'])

        # create plot only if numerical and not target variable
        if np.issubdtype(X_train.dtype, np.integer) or np.issubdtype(X.dtype, np.floating) and i != target:

            # create labeled scatter plot
            plt.scatter(X_train, y_train, color='#a63719')
            plt.title(f'{y_lbl} vs {feature}')
            plt.xlabel(feature)
            plt.ylabel(y_lbl)
            
            # add path to return list and save figure to path
            image_path = f'graphs/{request.user.username}{i}.png'
            image_paths.append(image_path)

            plt.savefig(f'{settings.MEDIA_ROOT}/{image_path}')
            plt.clf()

            # TODO: save image as file instance
            # graph = Graph(request.user)
            # graph.image.name = f'{image_path}'
            # graph.save()

            
    
    return image_paths
