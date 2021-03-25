from django.urls import path

from . import views

app_name = 'ui'
urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.index, name='register'),
    path('login', views.login, name='login'),
    path('process', views.upload_file, name='file_upload'),
    path('encrypt/<slug:sensitivity>', views.encrypt, name='encrypt')
]