from django.urls import path
from . import views
from django.shortcuts import redirect


urlpatterns = [
    # ENTIDADES
    path('', lambda request: redirect('entidade_list')),
    path("entidades/", views.EntidadeListView.as_view(), name="entidade_list"),
    path("entidades/nova/", views.EntidadeCreateView.as_view(), name="entidade_create"),
    path("entidades/<int:pk>/editar/", views.EntidadeUpdateView.as_view(), name="entidade_update"),
    path("entidades/<int:pk>/", views.EntidadeDetailView.as_view(), name="entidade_detail"),

    # DISTRIBUIÇÃO DE FICHAS
    path("entidades/<int:entidade_id>/distribuir/", views.distribuir_fichas, name="distribuir_fichas"),

    # BLOCOS
    path("blocos/", views.BlocoListView.as_view(), name="bloco_list"),
    path("blocos/novo/", views.BlocoCreateView.as_view(), name="bloco_create"),
    path("blocos/<int:pk>/", views.BlocoDetailView.as_view(), name="bloco_detail"),
]
