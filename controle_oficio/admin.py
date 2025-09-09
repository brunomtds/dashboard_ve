from django.contrib import admin
from .models import Entidade, Bloco, Ficha

# Inline para mostrar as Fichas dentro da página de detalhes de um Bloco
class FichaInline(admin.TabularInline):
    model = Ficha
    extra = 0  # Não mostra formulários extras para adicionar novas fichas por aqui
    readonly_fields = ('numero', 'tipo', 'status', 'entidade', 'data_recebimento', 'data_entrega', 'data_desfecho')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Desabilita a opção de adicionar fichas a partir do bloco, pois são criadas automaticamente
        return False

@admin.register(Entidade)
class EntidadeAdmin(admin.ModelAdmin):
    """
    Customização do admin para o modelo Entidade.
    """
    list_display = ('nome', 'tipo', 'tipo_documento', 'numero_documento')
    search_fields = ('nome', 'numero_documento')
    list_filter = ('tipo', 'tipo_documento')
    ordering = ('nome',)

@admin.register(Bloco)
class BlocoAdmin(admin.ModelAdmin):
    """
    Customização do admin para o modelo Bloco.
    Inclui uma visualização das fichas associadas.
    """
    list_display = ('id', 'numero_inicial', 'tipo', 'data_recebimento')
    list_filter = ('tipo',)
    search_fields = ('numero_inicial',)
    ordering = ('-data_recebimento',)
    inlines = [FichaInline] # Adiciona a tabela de fichas na página do bloco

@admin.register(Ficha)
class FichaAdmin(admin.ModelAdmin):
    """
    Customização do admin para o modelo Ficha.
    """
    list_display = ('numero', 'tipo', 'status', 'entidade', 'bloco_link', 'data_entrega', 'data_desfecho')
    list_select_related = ('entidade', 'bloco') # Otimiza a busca dos dados relacionados
    search_fields = ('numero', 'entidade__nome')
    list_filter = ('status', 'tipo', 'entidade', 'bloco')
    list_editable = ('status',) # Permite editar o status diretamente na lista
    readonly_fields = ('numero', 'tipo', 'bloco', 'data_recebimento', 'data_desfecho', 'desfecho_por')
    ordering = ('numero',)
    
    def bloco_link(self, obj):
        # Cria um link para a página do bloco na lista de fichas
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:controle_oficio_bloco_change", args=[obj.bloco.id])
        return format_html('<a href="{}">{}</a>', link, obj.bloco.numero_inicial)
    bloco_link.short_description = 'Bloco de Origem'