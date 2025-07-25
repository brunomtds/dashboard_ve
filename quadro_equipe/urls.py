from django.urls import path
from . import views

app_name = 'quadro_equipe'

urlpatterns = [
    path('', views.quadro_funcionarios, name='quadro_funcionarios'),
    path('adicionar/', views.adicionar_funcionario, name='adicionar_funcionario'),
    path('editar/<int:funcionario_id>/', views.editar_funcionario, name='editar_funcionario'),
    path('excluir/<int:funcionario_id>/', views.excluir_funcionario, name='excluir_funcionario'),
    path('adicionar_responsabilidade/', views.adicionar_responsabilidade, name='adicionar_responsabilidade'),
]
