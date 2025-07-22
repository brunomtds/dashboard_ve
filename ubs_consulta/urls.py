from django.urls import path
from . import views

app_name = 'ubs_consulta'

urlpatterns = [
    path('', views.consulta_cep_view, name='consulta_cep'),
]