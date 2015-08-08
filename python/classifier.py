__author__ = 'Nimrod Shneor'

import cv2 as cv
from componentExtractor import componentExtractor
import numpy as np
from sklearn.svm import SVC
import csv
from featureExtractor import featureExtractor
import matplotlib.pyplot as plt
from sklearn.naive_bayes import GaussianNB
from sklearn.decomposition import PCA
from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import classification_report
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn import cross_validation
from sklearn import metrics
from lasagne import layers
from lasagne.updates import nesterov_momentum


# TODO:
# 1. Add cross validation to tune SVM parameters in posNeg Decomposition method.
# 2. Add more images to validation set from different samples
# 3. Start Exploring Neural-Network as a classifier for posNeg Decomposition / Specie Classification.

class classifier:

    def __init__(self, inputImage = None):
        self._image = inputImage
        self.X = None
        self.y = None

    def plotPCA(self,Dataset):
        npzfile = np.load(Dataset)
        trainingData = npzfile['arr_0']
        labels = npzfile['arr_1']
        classes = npzfile['arr_2']

        X = trainingData
        y = classes

        print np.shape(X)

        X_new = SelectKBest(chi2, k=30).fit_transform(X, y)

        pca = PCA(n_components=2)
        X_r = pca.fit(X_new).transform(X_new)

        for c, i, target_name in zip("rgb", [0, 1], ["negative","positive"]):
             plt.scatter(X_r[y == i, 0], X_r[y == i, 1], c=c, label=target_name)
        plt.legend()
        plt.title('PCA')
        plt.xticks([])
        plt.yticks([])
        plt.show()

    def validation(self, val_images, Dataset):
        '''
        Main Validation function to validate model on
        :param val_images:
        :param Dataset: Path to a given dataset in the format of npz. see datasetOrginizer Class.
        :return:
        '''

        npzfile = np.load(Dataset)
        trainingData = npzfile['arr_0']
        labels = npzfile['arr_1']
        classes = npzfile['arr_2']
        max_min_features = npzfile['arr_3']

        X = trainingData
        y = classes

        clf = SVC(C=1.0, cache_size=200, class_weight=None, coef0=0.0, degree=3,
            gamma=0.0, kernel='linear', max_iter=-1, probability=False,
            random_state=None, shrinking=True, tol=0.001, verbose=False)        
        clf.fit(X,y)

        fig, axes = plt.subplots(nrows=10, ncols=10)

        test_set = val_images
        for i,num in enumerate(test_set):
            #print num
            im = cv.imread("..//Samples//Validation_Set//" + str(num) + ".jpg")
            fe = featureExtractor(im)
            feature_vector = fe.computeFeatureVector()
            # Normalize feature vector
            for k, num in enumerate(feature_vector):
                #max_feature = max_min_features[k][0]
                #min_feature = max_min_features[k][1]
                #feature_vector[k] = (feature_vector[k] - min_feature) / (max_feature - min_feature)
                feature_vector[k] = 1/(1+np.exp(feature_vector[k]))

            res = clf.predict(feature_vector)
            print res

            plt.subplot(10,10,i)
            plt.imshow(im)
            plt.xticks([])
            plt.yticks([])

            if res[0] == 1:
                plt.title('positive')
                # cv.namedWindow("positive" + str(num),cv.WINDOW_NORMAL)
                # cv.imshow("positive" + str(num),im)
            else:
                plt.title('negative')
                # cv.namedWindow("negative" + str(num),cv.WINDOW_NORMAL)
                # cv.imshow("negative" + str(num),im)
        
        fig.subplots_adjust(hspace=.5)
        
        plt.show()    

    def posNegDecompose(self, Dataset):
        '''
        :param Dataset: The dataset used to create the model.
         This function returns list of 'objects of interest': e.g. suspected forams.
        :return:
        '''

        npzfile = np.load(Dataset)
        trainingData = npzfile['arr_0']
        labels = npzfile['arr_1']
        classes = npzfile['arr_2']
        max_min_features = npzfile['arr_3']

        X = trainingData
        y = classes

        ### Segmentation
        ce = componentExtractor(self._image)
        components = ce.extractComponents() # THIS IS A LIST

        ### Model Building 
        clf = SVC(C=1.0, cache_size=200, class_weight=None, coef0=0.0, degree=3,
            gamma=0.0, kernel='linear', max_iter=-1, probability=False,
            random_state=None, shrinking=True, tol=0.001, verbose=False)        
        clf.fit(X,y)

        for i, component in enumerate(components):
            fe = featureExtractor(component[0])
            feature_vector = fe.computeFeatureVector()
            # Normalize feature vector
            for k, num in enumerate(feature_vector):
                #max_feature = max_min_features[k][0]
                #min_feature = max_min_features[k][1]
                #feature_vector[k] = (feature_vector[k] - min_feature) / (max_feature - min_feature)
                feature_vector[k] = 1/(1+np.exp(feature_vector[k]))

            res = clf.predict(feature_vector)
            print res
            
            if res[0] == 1:
                x,y,w,h = component[1]
                cv.rectangle(self._image,(x,y),(x+w,y+h),(0,255,0),2)

        
        cv.namedWindow("positive",cv.WINDOW_NORMAL)
        cv.imshow("positive",self._image)

        cv.waitKey()

    def crossValidateGridSearch(self,Dataset):
        '''
        :param Dataset: The dataset used to create the model.
        This function is used to cross validate the model using Grid Search Method.
        :return:
        '''        

        npzfile = np.load(Dataset)
        trainingData = npzfile['arr_0']
        labels = npzfile['arr_1']
        classes = npzfile['arr_2']
        max_min_features = npzfile['arr_3']

        X = trainingData
        y = classes

        # Split the dataset in two equal parts
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.5, random_state=0)

        # Set the parameters by cross-validation
        tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-3, 1e-4],
                             'C': [1, 10, 100, 1000]},
                            {'kernel': ['linear'], 'C': [1, 10, 100, 1000]}]

        scores = ['precision', 'recall']

        for score in scores:
            print("# Tuning hyper-parameters for %s" % score)

            clf = GridSearchCV(SVC(C=1), tuned_parameters, cv=5,
                               scoring='%s' % score)
            clf.fit(X_train, y_train)

            print("Best parameters set found on development set:")
            print()
            print(clf.best_params_)
            print()
            print("Grid scores on development set:")
            print()
            for params, mean_score, scores in clf.grid_scores_:
                print("%0.3f (+/-%0.03f) for %r"
                      % (mean_score, scores.std() * 2, params))
            print()

            print("Detailed classification report:")
            print()
            print("The model is trained on the full development set.")
            print("The scores are computed on the full evaluation set.")
            print()
            y_true, y_pred = y_test, clf.predict(X_test)
            print(classification_report(y_true, y_pred))
            print()

    def classifieSample(self, Dataset='binData/Default.npz'):
        '''
        :param Dataset: The dataset used to create the model.
         Main Classifier Function. This function classifies 'Potential Forams' to their different species after posNegDecompose has be used to distinguish between positive and negative components.
        :return:
        '''

        npzfile = np.load(Dataset)
        trainingData = npzfile['arr_0']
        labels = npzfile['arr_1']
        classes = npzfile['arr_2']

        self.X = trainingData
        self.y = classes

        ## Segmentation
        ce = componentExtractor(self._image)
        components = ce.extractComponents # THIS IS A LIST


        for i,component in enumerate(components):

            fe = featureExtractor(component[i])
            morphoType = fe.computeMorphtypeNumber(components[i])
            filters = fe.buildGaborfilters()
            results = fe.processGabor(component,filters)
            feature_vector = fe.computeMeanAmplitude(results)
            feature_vector.append(morphoType)


