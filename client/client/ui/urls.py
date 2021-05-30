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
    path('stock', views.enter_stock, name='enter_stock'),
    path('delete', views.delete_all, name='delete_all'),
    path('view/stock', views.view_stock, name='view_stock'),
    path('request/<slug:bg>/<slug:location>', views.request_donor, name='request_donor'),
    path('api/view/stock/<slug:bg>/<slug:location>/', views.api_view_stock, name='api_view_stock'),
    path('api/view/donor/<slug:bg>/<slug:location>', views.api_view_donor, name='api_view_donor')
]