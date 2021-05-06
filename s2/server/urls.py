from django.urls import path

from . import views

urlpatterns = [
    path('S2/register', views.index, name='index'),
    path('S2/login', views.login, name='login'),
]