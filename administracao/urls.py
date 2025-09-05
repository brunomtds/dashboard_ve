from django.urls import path
from . import views

app_name = 'administracao'

urlpatterns = [
    path('', views.adm_dashboard_view, name='dashboard'),
    path('solicitacoes/', views.SolicitacaoListView.as_view(), name='solicitacao_list'),

    path('solicitacoes/<int:pk>/aprovar/', views.aprovar_solicitacao, name='solicitacao_aprovar'),
    path('solicitacoes/<int:pk>/rejeitar/', views.rejeitar_solicitacao, name='solicitacao_rejeitar'),
]