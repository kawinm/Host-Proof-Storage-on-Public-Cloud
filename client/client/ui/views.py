from django.shortcuts import render, redirect

import time
# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

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

BANKID_TO_URL = {
    "2522": "127.0.0.1"
}

def get_db_container(container_id):
    endpoint = "https://kawin.documents.azure.com:443/"
    key = 'U6VUfkGeu2vzNVKumpXsTWHkPyjbYi9ffmHmmsz9XUz6mqAwwcFTs7FAAzmb4ZF3SptDLFfs2vbCALrzimiJNQ=='

    client = CosmosClient(endpoint, key)

    id = "hpsdb"
    try:
        db = client.get_database_client(id)
        print('Database with id \'{0}\' was found, it\'s link is {1}'.format(id, db.database_link))

    except exceptions.CosmosResourceNotFoundError:
        print('A database with id \'{0}\' does not exist'.format(id))

    id = container_id
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
            bankname = form.cleaned_data['bank_name']
            location = form.cleaned_data['location']

            start_time = time.time()

            res = generate_keys(password)           

            # if username exits in db:
            #     change username
            #     return
            
            #s1(res, username)
            query = {
                'g2powP': res['g2powP'],
                'p': res['p'],
                'username': username,
                'g1': res['g1'],
                'g2': res['g2'],
                'x1': res['x1'],
                'a1': res['a1'],
                'a2': res['a2'],
                'b1': res['b1'],
                'y2': res['y2'],
                'func': 'register',
                'bankname': bankname,
                'location': location
            }
            print(query)
            response_s1 = requests.get('http://localhost:8085/S1/register', json = query)
            print(response_s1.json())

            g3 = response_s1.json().get("g3")
            g4 = response_s1.json().get("g4")

            query = {
                'g2powP': res['g2powP'],
                'p': res['p'],
                'username': username,
                'g1': res['g1'],
                'g2': res['g2'],
                'g3': g3,
                'g4': g4,
                'x2': res['x2'],
                'a1': res['a1'],
                'a2': res['a2'],
                'b2': res['b2'],
                'y1': res['y1'],
                'func': 'register',
                'bankname': bankname,
                'location': location
            }
            print(query)
            response_s2 = requests.get('http://localhost:8086/S2/register', json = query)
            print(response_s2.json())
            
            bankid = response_s1.json().get("id") + '-' + response_s2.json().get("id")

            user = User(user_name=username, p=res['p'], g1=res['g1'], g2=res['g2'], bank_name = bankname, location = location, bank_id = bankid)
            user.save()
            
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
            print("--- %s seconds ---" % (time.time() - start_time))    
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

            start_time = time.time()

            P = PasswordToHex(password)
            #user = User.objects.filter(user_name=username)
            user = User.objects.get(user_name=username)
            p = user.p 
            g1= user.g1 
            g2 = user.g2
            print("Prime", user.p)
            print("G1", user.g1) 
            print("G2", user.g2)  

            r = int(find_primitive_root(int(p)))

            R1 = modexp(int(g1), int(r), int(p))

            R2 = modexp(int(g2), int(P), int(p))
            query = {
                'username': username,
                'func': 'login',
                'R1': R1,
                'R2': R2
            }
            print(query)
            response = requests.get('http://localhost:8085/S1/login', json = query)
            print(response.json())

            print("--- %s seconds ---" % (time.time() - start_time))    
            
            if response.json()['msg'] == "success":
                request.session['username'] = username
                request.session['key'] = response.json()['key']
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

def handle_uploaded_file(request, f, password, action):
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


    print(type(df))
    # First let us encrypt secret message
    if 'username' in request.session and 'key' in request.session:
        username  = request.session["username"]
        key       = request.session["key"]
    else:
        return redirect('ui:login')

    user = User.objects.get(user_name=username)
    bankid = user.bank_id

    container = get_db_container(action)
    start_time = time.time()
    key  = request.session["key"]
    for i in range(0,55):
        data = {}
        salt = get_random_bytes(AES.block_size)
        private_key = hashlib.scrypt(key.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
        for j in range(len(col_names)):
            if r_pred[j] == 1:
                if col_names[j] == "id":
                    encrypted = encrypt_message(df.at[i+1, col_names[j]], private_key, salt)
                    data["did"] = encrypted
                else:
                    encrypted = encrypt_message(df.at[i+1, col_names[j]], private_key, salt)
                    data[col_names[j]] = encrypted
            else:
                data[col_names[j]] = str(df.at[i+1, col_names[j]])
        #print(data)
        data["salt"] = b64encode(salt).decode('utf-8')
        #print(data["did"], salt, data["salt"], private_key)
        data["id"] = uuid4().hex
        data["bankid"] = bankid
        
        container.create_item(body=data)
    print("--- %s seconds ---" % (time.time() - start_time))    
    return df, r_pred, col_names

def encrypt_message(plain_text, key, salt):
    plain_text = str(plain_text)
    # generate a random salt
    #salt = get_random_bytes(AES.block_size) 16

    # use the Scrypt KDF to get a private key from the password
    #private_key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    
    # create cipher config
    cipher_config = AES.new(key, AES.MODE_GCM)

    # return a dictionary with the encrypted text
    cipher_text, tag = cipher_config.encrypt_and_digest(bytes(plain_text, 'utf-8'))
    return {
        'cipher_text': b64encode(cipher_text).decode('utf-8'),
        'nonce': b64encode(cipher_config.nonce).decode('utf-8'),
        'tag': b64encode(tag).decode('utf-8')
    }

def upload_file(request):
    if 'key' in request.session:
        key  = request.session["key"]
    else:
        return redirect('ui:login')
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            password = form.cleaned_data['password']
            df, sensitivity, col_names = handle_uploaded_file(request, request.FILES['file'], password, "donor")
            
            request.session["file_upload"] = 1
            return redirect('ui:main')
    else:
        form = UploadFileForm()
    return render(request, 'ui/upload.html', {'form': form})


def decrypt_message(enc_dict, key, salt):
    # decode the dictionary entries from base64
    cipher_text = b64decode(enc_dict['cipher_text'])
    nonce = b64decode(enc_dict['nonce'])
    tag = b64decode(enc_dict['tag'])

    # generate the private key from the password and salt
    #private_key = hashlib.scrypt(key.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    # create the cipher config
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    # decrypt the cipher text
    decrypted = cipher.decrypt_and_verify(cipher_text, tag)

    
    return str(decrypted)[2:-1]

def main(request):
    if "file_upload" in request.session:
        if request.session["file_upload"] == 1:
            request.session["file_upload"] = 0
            return render(request, 'ui/main.html', {"msg": "File Uploaded Successfully"})
    return render(request, 'ui/main.html')

#def get_donor_data(blood_group, city):

def find_donor(request):
    if 'key' in request.session:
        secret_key  = request.session["key"]
    else:
        return redirect('ui:login')
    if request.method == "POST":
        form = FindDonorForm(request.POST)

        if form.is_valid():
            blood_group = form.cleaned_data['blood_group']
            city = form.cleaned_data['city']

            query = "SELECT * FROM c WHERE c.blood_group = '"+ blood_group +"' and c.district = '"+ city +"'"

            container = get_db_container("donor")
            data = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            #print(data)
            dec_resp = []
            start_time = time.time()
            for i in data:
                dec_data = {}
                salt = b64decode(i['salt'])
                private_key = hashlib.scrypt(secret_key.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
                for key, value in i.items():
                    if key == "salt":
                        break
                    if type(value) is dict:
                        dec_data[key] = decrypt_message(value, private_key, salt)
                    else:
                        dec_data[key] = value
                    if dec_data[key] == "nan":
                        dec_data[key] = "-"
                dec_resp.append(dec_data)

            print("--- %s seconds ---" % (time.time() - start_time))
            print(dec_resp)
            return render(request, 'ui/show_donor.html', {'headers':dec_resp[0], 'data': dec_resp, 'bg':blood_group, 'location':city})
    form = FindDonorForm()
    return render(request, 'ui/find.html', {'form': form})

def enter_stock(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            password = form.cleaned_data['password']
            df, sensitivity, col_names = hand
            request.session["file_upload"] = 1
            return redirect('ui:main')
    else:
        form = UploadFileForm()
    return render(request, 'ui/upload.html', {'form': form})

def view_stock(request):

    if 'username' in request.session:
        username  = request.session["username"]
    else:
        return redirect('ui:login')

    user = User.objects.get(user_name=username)
    bankid = user.bank_id

    query = "SELECT * FROM c WHERE c.bankid = '"+ bankid +"'"

    container = get_db_container("stock")
    password = "kawin"
    data = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    print(data)
    dec_data = {}
    for i in data:
        for key, value in i.items():
            if type(value) is dict:
                dec_data[key] = decrypt_message(value, password)
            else:
                dec_data[key] = value
    print(dec_data)
    return render(request, 'ui/view_stock.html', {'data': dec_data})

def request_donor(request, bg, location):
    query = "SELECT bankid FROM c WHERE c.blood_group = '"+ bg +"' and c.location = '"+ location +"'"

    container = get_db_container("donor")
    password = "kawin"
    data = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
    dec_data = {}
    for bank in data:
        query = "SELECT bankname FROM c WHERE c.bankid = '"+ bank +"'"
        container = get_db_container("users")
        password = "kawin"
        data = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
        ))
        dec_data[bank] = data[0]

    return render(request, 'ui/request_donor.html', {'data': dec_data})

def api_view_stock(request, bg, location):
    if 'username' in request.session:
        username  = request.session["username"]
    else:
        return redirect('ui:login')

    user = User.objects.get(user_name=username)
    bankid = user.bank_id
    bankname = user.bank_name

    
    if bg[-1] == "p":
        bg = bg[:-1] + "+"
    elif bg[-1] == "m":
        bg = bg[:-1] + "-"

    query = "SELECT c.blood_group, c.quantity, c.location, c.donated_on FROM c WHERE c.bankid = '"+ bankid +"' and c.blood_group = '"+ bg +"' and c.location = '"+ location +"'"

    print(query)

    container = get_db_container("stock")
    password = "kawin"
    data = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    print(data)
    json_data = {}
    dec_data = {}
    cnt = 1
    for i in data:
        for key, value in i.items():
            if type(value) is dict:
                dec_data[key] = decrypt_message(value, password)
            else:
                dec_data[key] = value
            dec_data["bankname"] = bankname
        json_data[cnt] = dec_data
        cnt+=1
    print(json_data)
    return JsonResponse(json_data)

def api_view_donor(request, bg, location):
    if bg[-1] == "p":
        bg = bg[:-1] + "+"
    elif bg[-1] == "m":
        bg = bg[:-1] + "-"

    query = "SELECT * FROM c WHERE c.bankid = '"+ bankid +"' and c.blood_group = '"+ bg +"' and c.location = '"+ location +"'"

    print(query)
    

    container = get_db_container("donor")
    password = "kawin"
    data = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
    print(data)
    dec_data = {}
    for i in data:
        for key, value in i.items():
            if type(value) is dict:
                dec_data[key] = decrypt_message(value, password)
            else:
                dec_data[key] = value
    print(dec_data)
    return JsonResponse(dec_data)

def delete_all(request):
    query = "SELECT * FROM c "
    
    container = get_db_container("donor")
    data = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
    for i in data:
        response = container.delete_item(item=i["id"], partition_key=i["state"])
    return "<p>OK</p>"
