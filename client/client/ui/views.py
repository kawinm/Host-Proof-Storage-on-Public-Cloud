from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect

from .forms import RegisterForm, LoginForm, UploadFileForm
from .elgamal import *

import numpy as np # linear algebra
import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder

def s1(request):
    g4powg2powP = modexp(request['g4'], request['g2powP'], request['p'])
    g4pow2powP_str = str(g4powg2powP)
    length = len(g4pow2powP_str)
    length_for_x = length // 9
    rem = length - length_for_x
    vertex = []
    for i in range(9):
        x = int(g4pow2powP_str[i*length_for_x: i*length_for_x + length_for_x])
        vertex.append(x)
    u4 = int(g4pow2powP_str[length_for_x*9: ])
    x4 = (vertex[0] + vertex[3] + vertex[6]) / 3 + u4
    y4 = (vertex[1] + vertex[4] + vertex[7]) / 3 + u4
    z4 = (vertex[2] + vertex[5] + vertex[8]) / 3 + u4
    vertex.append(x4)
    vertex.append(y4)
    vertex.append(z4)
    A = [[0,0,0],[0,0,0],[0,0,0]]
    A[0][0] = vertex[3] - vertex[0]
    A[1][0] = vertex[4] - vertex[1]
    A[2][0] = vertex[5] - vertex[2]

    A[0][1] = vertex[6] - vertex[3]
    A[1][1] = vertex[7] - vertex[4]
    A[2][1] = vertex[8] - vertex[5]

    A[0][2] = x4 - vertex[6]
    A[1][2] = y4 - vertex[7]
    A[2][2] = z4 - vertex[8]

    B = [[0],[0],[0]]
    B[0][0] = ((vertex[3]+vertex[4]+vertex[5]) - (vertex[0]+vertex[1]+vertex[2])) * 0.5
    B[1][0] = ((vertex[6]+vertex[7]+vertex[8]) - (vertex[3]+vertex[4]+vertex[5])) * 0.5
    B[2][0] = ((x4+y4+z4) - (vertex[6]+vertex[7]+vertex[8])) * 0.5

    A_inv = getMatrixInverse(A)

    omega = matrix_multiplication(A_inv, B)
    print('A ', A)
    print('A inv ', A_inv)
    print('B ', B)
    print('Omega ', omega)


def index(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['user_name']
            password = form.cleaned_data['password']

            res = generate_keys(password)           

            s1(res)
            
            #Sending confirmation mail 
            """ current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('user/acc_active_email.html', {
                    'user': post,
                    'domain': current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(post.pk)),
                    'token':account_activation_token.make_token(post),
            })
            to_email = form.cleaned_data.get('email_id')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration') """
            return redirect('ui:login')
        else:
            message = 'Username is already registered.'
            form = RegisterForm()
            return render(request, 'ui/index.html', {'form': form, 'message':message})
    else:
        form = RegisterForm()
        return render(request, 'ui/index.html', {'form': form})

def handle_uploaded_file(f):
    df = pd.read_csv(f)
    row, col = df.shape 
    col_names = list(df.columns)

    data_type = df.dtypes
    print("[STATUS] Found Data Type")

    null_per = df.isna().sum() / row * 100
    print("[STATUS] Calculated Percentage of NULL values")

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
    print("[STATUS] Calculated Percentage of Unique values")
    print("[STATUS] Found Categorical data")

    le = LabelEncoder()
    le.fit([1, 2, 2, 6])

    encdf = df
    for i in col_names:
        if encdf[i].dtype == 'object':
            encdf[i] = le.fit_transform(df[i].astype('str'))

    corrMatrix = encdf.corr()
    corr = [0 for i in range(col)]
    for i in range(col):
        for j in range(i-1):
            if corrMatrix[col_names[i]][col_names[j]] > 0.75 or corrMatrix[col_names[i]][col_names[j]] < -0.75:
                corr[i] = 1
    print("[STATUS] Calculated Correlation Matrix")

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
    print("[STATUS] Found Pattern based Sensitive data")

    X_pred = np.zeros([col, 6], dtype=int)

    for i in range(col):
        for j in range(6):
            if j == 0:
                if data_type[i] == 'int':
                    X_pred[i][0] = 1
                elif data_type[i] == 'float':
                    X_pred[i][0] = 2
                elif data_type[i] == 'object':
                    X_pred[i][0] = 3
                else:
                    X_pred[i][0] = 4
            elif j == 1:
                X_pred[i][1] = int(null_per[i] * 100)
            elif j == 2:
                X_pred[i][2] = unique_per[i]
            elif j == 3:
                X_pred[i][3] = categorical[i]
            elif j == 4:
                X_pred[i][4] = corr[i]
            elif j == 5:
                X_pred[i][5] = sensitive[i]

    print("[STATUS] Data Analyzed Successfully")

    filename = './finalized_model (2).sav'

    loaded_model = pickle.load(open(filename, 'rb'))

    r_pred = loaded_model.predict(X_pred)

    print("[STATUS] Sensitivity Prediction Successfull")
    return r_pred

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            sensitivity = handle_uploaded_file(request.FILES['file'])
            return redirect('encrypt', sensitivity)
    else:
        form = UploadFileForm()
    return render(request, 'ui/upload.html', {'form': form})

