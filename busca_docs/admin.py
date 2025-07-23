from django.contrib import admin
from .models import Categoria, Tag, Documento


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_publicacao', 'ativo', 'data_cadastro')
    list_filter = ('categoria', 'ativo', 'data_publicacao', 'data_cadastro', 'tags')
    search_fields = ('titulo', 'descricao')
    filter_horizontal = ('tags',)
    date_hierarchy = 'data_cadastro'
    ordering = ('-data_cadastro',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'descricao', 'categoria')
        }),
        ('Arquivo e Publicação', {
            'fields': ('arquivo', 'data_publicacao')
        }),
        ('Classificação', {
            'fields': ('tags', 'ativo')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('categoria').prefetch_related('tags')

