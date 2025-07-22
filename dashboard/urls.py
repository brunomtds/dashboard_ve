from django.urls import path
from . import views

app_name = 'dashboard'  # Define the namespace

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
]