from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect

from .forms import FindDonorForm

import requests
import json

from azure.cosmos import exceptions, CosmosClient, PartitionKey
from uuid import uuid4

BANKID_TO_URL = {
    "688212818ad04221ad9dc30177e3452a":"127.0.0.1:8080"
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
        form = FindDonorForm(request.POST)

        if form.is_valid():
            blood_group = form.cleaned_data['blood_group']
            location = form.cleaned_data['location']

            query = "SELECT bankid FROM c WHERE c.blood_group = '"+ blood_group +"' and c.location = '"+ location +"'"

            container = get_db_container("stock")
            password = "kawin"
            data = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            dec_data = {}
            for bank in data:
                url = BANKID_TO_URL[bank] + "/api/view/stock/" + blood_group + "/" + location
                response = requests.get(url)
                print(response.json())

                dec_data += json.load(response.json())

            return render(request, 'ui/show_donor.html', {'data': dec_data})
    form = FindDonorForm()
    return render(request, 'ui/index.html', {'form': form})