from django.contrib import admin
from .models import SolicitacaoAcesso

@admin.register(SolicitacaoAcesso)
class SolicitacaoAcessoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'ramal', 'departamento', 'aprovado', 'criado_em')
    list_filter = ('aprovado', 'departamento')
    search_fields = ('nome', 'email', 'ramal')
    list_editable = ('aprovado',)
    ordering = ('-criado_em',)