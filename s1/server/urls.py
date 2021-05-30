from django.urls import path

from . import views

urlpatterns = [
    path('S1/register', views.index, name='index'),
    path('S1/login', views.login, name='login'),
]