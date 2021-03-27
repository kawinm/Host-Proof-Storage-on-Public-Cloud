from django.urls import path

from . import views

app_name = 'ui'
urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.index, name='register'),
    path('login', views.login, name='login'),
    path('upload', views.upload_file, name='upload'),
    path('find', views.find_donor, name='find'),
    path('main', views.main, name='main'),
    path('encrypt/<slug:sensitivity>', views.encrypt, name='encrypt')
]