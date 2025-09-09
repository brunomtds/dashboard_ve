from django.urls import path
from . import views

app_name = 'administracao'

urlpatterns = [
    path('', views.adm_dashboard_view, name='dashboard'),
    path('solicitacoes/', views.SolicitacaoListView.as_view(), name='solicitacao_list'),

    # Gestão de solicitações
    path('solicitacoes/<int:pk>/aprovar/', views.aprovar_solicitacao, name='solicitacao_aprovar'),
    path('solicitacoes/<int:pk>/rejeitar/', views.rejeitar_solicitacao, name='solicitacao_rejeitar'),

    # Gestão de usuários
    path('usuarios/', views.UserListView.as_view(), name='user_list'),
    path('usuarios/<int:pk>/toggle-active/', views.toggle_user_active_status, name='user_toggle_active'),
     path('usuarios/<int:pk>/force-password-change/', views.force_password_change, name='user_force_password_change'),
]