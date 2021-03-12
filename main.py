import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import matplotlib.pyplot as plt
#import pandas_profiling

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
#for dirname, _, filenames in os.walk('/kaggle/input'):
#    for filename in filenames:
#        print(os.path.join(dirname, filename))

# You can write up to 5GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All" 
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session

df = pd.read_csv('abc.csv')

#print(df.at[10, 'firstname'])
#Getting Number of rows and cols
row, col = df.shape 
print(row,col)

#Getting Names of all columns into a list
col_names = list(df.columns)

#Getting Datatype of each column into a Pandas series
data_type = df.dtypes
print(data_type)
#int, float, string, date, image
#Percentage of Null values in each column
null_per = df.isna().sum() / row * 100
print(null_per)

#Percentage of Unique values in each column
#Approximate if a column is categorical or not
unique_per = []
categorical = []
for c in col_names:
    b = df.pivot_table(index=[c], aggfunc='size')
    unique =0
    for i in b.array:
        if i == 1:
            unique+=1
    col_unique_per = unique / row * 100
    if col_unique_per <= 2:
        categorical.append(1)
    else:
        categorical.append(0)
    unique_per.append(col_unique_per)
print(unique_per)
print(categorical)

#Default value && Present or not

#Find Correlation Matrix for numerical data
corrMatrix = df.corr()
print (corrMatrix)

#Pattern Matching to find if a column is important
sensitive = []
patterns = ["id", "aadhaar", "ssn", "name", "phone", "address", "mail","location"]
for c in col_names:
    f = 0
    c = c.lower()
    for pattern in patterns:
        if pattern in c:
            sensitive.append(1)
            f = 1
            break
    if f == 0:
        sensitive.append(0)
print(sensitive)

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import pickle

X_test = [[1, 70, 20, 0, 1, 0]]
filename = 'finalized_model.sav'
loaded_model = pickle.load(open(filename, 'rb'))
r_pred = loaded_model.predict(X_test)
print(r_pred)
print(r_pred.round())
