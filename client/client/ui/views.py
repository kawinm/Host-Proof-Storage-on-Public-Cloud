from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect

from .forms import RegisterForm, LoginForm, UploadFileForm, FindDonorForm
from .elgamal import *
from .models import User, Server

import numpy as np # linear algebra
import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder

from base64 import b64encode, b64decode
import hashlib
from Cryptodome.Cipher import AES
import os
from Cryptodome.Random import get_random_bytes

from math import acos, degrees

import requests
import json

from azure.cosmos import exceptions, CosmosClient, PartitionKey
from uuid import uuid4

def get_db_container():
    endpoint = "https://kawin.documents.azure.com:443/"
    key = 'U6VUfkGeu2vzNVKumpXsTWHkPyjbYi9ffmHmmsz9XUz6mqAwwcFTs7FAAzmb4ZF3SptDLFfs2vbCALrzimiJNQ=='

    client = CosmosClient(endpoint, key)

    id = "hpsdb"
    try:
        db = client.get_database_client(id)
        print('Database with id \'{0}\' was found, it\'s link is {1}'.format(id, db.database_link))

    except exceptions.CosmosResourceNotFoundError:
        print('A database with id \'{0}\' does not exist'.format(id))

    id = "donor"
    try:
        container = db.get_container_client(id)
        print('Container with id \'{0}\' was found, it\'s link is {1}'.format(container.id, container.container_link))

    except exceptions.CosmosResourceNotFoundError:
        print('A container with id \'{0}\' does not exist'.format(id))

    return container

def index(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['user_name']
            password = form.cleaned_data['password']

            res = generate_keys(password)           

            try:
                user = User(user_name=username, p=res['p'], g1=res['g1'], g2=res['g2'])
                user.save()

                
            except:
                print("Username already exists")
            
            #s1(res, username)
            query = {
                'g2powP': res['g2powP'],
                'p': res['p'],
                'username': username,
                'g1': res['g1'],
                'g2': res['g2'],
                'func': 'register'
            }
            print(query)
            response = requests.get('http://localhost:7071/api/S1', json = query)
            print(response.json())
            
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

def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['user_name']
            password = form.cleaned_data['password']

            P = PasswordToHex(password)
            #user = User.objects.filter(user_name=username)
            user = User.objects.get(user_name=username)
            p = user.p 
            g1= user.g1 
            g2 = user.g2
            print("Prime", user.p)
            print("G1", user.g1) 
            print("G2", user.g2)  

            g2powP = modexp(int(g2), int(P), int(p))
            query = {
                'g2powP': g2powP,
                'username': username,
                'func': 'login'
            }
            print(query)
            response = requests.get('http://localhost:7071/api/S1', json = query)
            print(response.json())

            if response.json()['msg'] == "success":
                return redirect('ui:main')
            else:
                message = 'Wrong Username or Password'
                form = LoginForm()
                return render(request, 'ui/login.html', {'form': form, 'message':message})
        else:
            message = 'Username is already registered.'
            form = LoginForm()
            return render(request, 'ui/login.html', {'form': form, 'message':message})
    else:
        form = LoginForm()
        return render(request, 'ui/login.html', {'form': form})

def handle_uploaded_file(f, password):
    df = pd.read_csv(f)
    print(type(df))
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

    encdf = df.copy(deep=True)
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
    print(type(df))
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

    salt = b"1234567890"
    print(type(df))
    # First let us encrypt secret message
    for i in range(2, 15):
        data = {}
        for j in range(len(col_names)):
            if r_pred[j] == 1:
                if col_names[j] == "id":
                    encrypted = encrypt_message(df.at[i+1, col_names[j]], password, salt)
                    data["did"] = encrypted
                else:
                    encrypted = encrypt_message(df.at[i+1, col_names[j]], password, salt)
                    data[col_names[j]] = encrypted
            else:
                data[col_names[j]] = str(df.at[i+1, col_names[j]])
        print(data)
        data["id"] = uuid4().hex
        container = get_db_container()
        container.create_item(body=data)
    return df, r_pred, col_names

def encrypt_message(plain_text, password, salt):
    plain_text = str(plain_text)
    # generate a random salt
    #salt = get_random_bytes(AES.block_size) 16

    # use the Scrypt KDF to get a private key from the password
    private_key = hashlib.scrypt(
        password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    
    # create cipher config
    cipher_config = AES.new(private_key, AES.MODE_GCM)

    # return a dictionary with the encrypted text
    cipher_text, tag = cipher_config.encrypt_and_digest(bytes(plain_text, 'utf-8'))
    return {
        'cipher_text': b64encode(cipher_text).decode('utf-8'),
        'salt': b64encode(salt).decode('utf-8'),
        'nonce': b64encode(cipher_config.nonce).decode('utf-8'),
        'tag': b64encode(tag).decode('utf-8')
    }

def encrypt(df, sensitivity, col_names):
    password = "kawin"
    salt = b"1234567890"
    print(type(df))
    print(col_names[:5])
    # First let us encrypt secret message
    for i in range(5):
        data = {}
        for j in range(len(col_names)):
            if sensitivity[j] == "1":
                encrypted = encrypt(df.at[i+1, col_names[j]], password, salt)
                data[col_names[j]] = encrypted
            else:
                data[col_names[j]] = df.at[i+1, col_names[j]]
        print(data)

    # Let us decrypt using our original password
    decrypted = decrypt_message(encrypted, password)
    print(bytes.decode(decrypted))


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            password = form.cleaned_data['password']
            df, sensitivity, col_names = handle_uploaded_file(request.FILES['file'], password)
            sensi = "".join(map(str, sensitivity))
            print(sensi)
            #encrypt(df, sensi, col_names)
            return redirect('ui:encrypt', sensi)
    else:
        form = UploadFileForm()
    return render(request, 'ui/upload.html', {'form': form})


def decrypt_message(enc_dict, password):
    # decode the dictionary entries from base64
    salt = b64decode(enc_dict['salt'])
    cipher_text = b64decode(enc_dict['cipher_text'])
    nonce = b64decode(enc_dict['nonce'])
    tag = b64decode(enc_dict['tag'])
    

    # generate the private key from the password and salt
    private_key = hashlib.scrypt(
        password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    # create the cipher config
    cipher = AES.new(private_key, AES.MODE_GCM, nonce=nonce)

    # decrypt the cipher text
    decrypted = cipher.decrypt_and_verify(cipher_text, tag)

    return decrypted

def main(request):
    return render(request, 'ui/main.html')

#def get_donor_data(blood_group, city):

def find_donor(request):
    if request.method == "POST":
        form = FindDonorForm(request.POST)

        if form.is_valid():
            blood_group = form.cleaned_data['blood_group']
            city = form.cleaned_data['city']

            query = "SELECT * FROM c WHERE c.blood_group = '"+ blood_group +"' and c.district = '"+ city +"'"

            container = get_db_container()
            password = "kawin"
            data = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            print(data)
            dec_list = []
            for i in data:
                dec_data = {}
                for key, value in i.items():
                    if key == "id" or key[0] == "_":
                        continue
                    if type(value) is dict:
                        dec_data[key] = decrypt_message(value, password)
                    else:
                        dec_data[key] = value
                    if dec_data[key] == "nan":
                        dec_data[key] = "-"
                dec_list.append(dec_data)
            print(dec_list)
            return render(request, 'ui/show.html', {'data': dec_list})
    form = FindDonorForm()
    return render(request, 'ui/find.html', {'form': form})