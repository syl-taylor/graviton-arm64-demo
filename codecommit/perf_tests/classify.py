# Fragment code (classify.py) from https://www.dominodatalab.com/blog/credit-card-fraud-detection-using-xgboost-smote-and-threshold-moving 
# Dataset (creditcard.csv) from https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud 

import time
import random
from datetime import datetime
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

random.seed(1000)

dataDF = pd.read_csv("creditcard.csv")
dataDF["Hour"] = dataDF["Time"].apply(datetime.fromtimestamp).dt.hour

trainDF, testDF = train_test_split(dataDF, test_size=0.2, random_state=1234, stratify=dataDF[["Class"]])

trainDF_norm = trainDF.copy()
trainDF_norm["Amount"] = trainDF["Amount"].subtract(trainDF["Amount"].mean())
trainDF_norm["Hour"] = trainDF["Hour"].subtract(trainDF["Hour"].mean())
testDF_norm = testDF.copy()
testDF_norm["Amount"] = testDF["Amount"].subtract(testDF["Amount"].mean())
testDF_norm["Hour"] = testDF["Hour"].subtract(testDF["Hour"].mean())

trainDF = trainDF_norm
testDF = testDF_norm
trainDF = trainDF.drop(["Time"], axis=1)
testDF = testDF.drop(["Time"], axis=1)

X_train = trainDF.iloc[:, trainDF.columns != "Class"]
y_train = trainDF.iloc[:, trainDF.columns == "Class"]
X_test = testDF.iloc[:, testDF.columns != "Class"]
y_test = testDF.iloc[:, testDF.columns == "Class"]
X_train.head()

X_train_smote, y_train_smote = SMOTE(random_state=1234).fit_resample(X_train, y_train)

model = XGBClassifier(objective="binary:logistic", eval_metric="auc")

start_time = time.time()

model.fit(X_train_smote, y_train_smote)

print("\n\n")
print("Model Training --- %s seconds ---" % (time.time() - start_time))
print("\n\n")

start_time = time.time()

y_pred = model.predict_proba(X_test)[:,1]

print("Model Predict --- %s seconds ---" % (time.time() - start_time))
print("\n\n")
