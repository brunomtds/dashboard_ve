from django.urls import path
from . import views

app_name = 'busca_docs'

urlpatterns = [
    path('', views.busca_documentos, name='busca_documentos'),
    path('adicionar/', views.adicionar_documento, name='adicionar_documento'),
    path('documento/<int:documento_id>/', views.detalhes_documento, name='detalhes_documento'),
]

