from django.urls import path
from . import views
from django.shortcuts import redirect


urlpatterns = [
    # ENTIDADES
    path("", views.dashboard_view, name="controle_oficio_dashboard"),
    path("entidades/", views.EntidadeListView.as_view(), name="entidade_list"),
    path("entidades/nova/", views.EntidadeCreateView.as_view(), name="entidade_create"),
    path("entidades/<int:pk>/editar/", views.EntidadeUpdateView.as_view(), name="entidade_update"),
    path("entidades/<int:pk>/", views.EntidadeDetailView.as_view(), name="entidade_detail"),
    # DISTRIBUIÇÃO DE FICHAS
    path("entidades/<int:entidade_id>/distribuir/", views.distribuir_fichas, name="distribuir_fichas"),

    # FICHAS
    path("fichas/<int:ficha_id>/desfecho/", views.dar_desfecho_ficha, name="dar_desfecho_ficha"),
    path("fichas/desfecho-em-lote/", views.dar_desfecho_em_lote, name="dar_desfecho_em_lote"),
    path("fichas/transferir-em-lote/", views.transferir_fichas_em_lote, name="transferir_fichas_em_lote"),

    # BLOCOS
    path("blocos/", views.BlocoListView.as_view(), name="bloco_list"),
    path("blocos/novo/", views.BlocoCreateView.as_view(), name="bloco_create"),
    path("blocos/<int:pk>/", views.BlocoDetailView.as_view(), name="bloco_detail"),
]
