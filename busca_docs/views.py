from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Documento, Categoria, Tag
from .forms import DocumentoForm


def busca_documentos(request):
    """
    View principal para busca de documentos.
    Se não houver parâmetros de busca, exibe todos os documentos agrupados por categoria.
    """
    # Parâmetros de busca
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    tags_ids = request.GET.getlist('tags')
    
    # Busca base - apenas documentos ativos
    documentos = Documento.objects.filter(ativo=True)
    
    # Aplicar filtros se houver parâmetros
    filtros_aplicados = False
    
    # Filtro por texto livre (título e descrição)
    if query:
        documentos = documentos.filter(
            Q(titulo__icontains=query) | Q(descricao__icontains=query)
        )
        filtros_aplicados = True
    
    # Filtro por categoria
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            documentos = documentos.filter(categoria_id=categoria_id)
            filtros_aplicados = True
        except (ValueError, TypeError):
            pass
    
    # Filtro por tags
    if tags_ids:
        try:
            tags_ids = [int(tag_id) for tag_id in tags_ids if tag_id.isdigit()]
            if tags_ids:
                documentos = documentos.filter(tags__in=tags_ids).distinct()
                filtros_aplicados = True
        except (ValueError, TypeError):
            pass
    
    # Ordenação
    documentos = documentos.select_related('categoria').prefetch_related('tags')
    
    # Se não há filtros, agrupar por categoria
    documentos_agrupados = {}
    if not filtros_aplicados:
        # Agrupar documentos por categoria
        categorias = Categoria.objects.all()
        for categoria in categorias:
            docs_categoria = documentos.filter(categoria=categoria)
            if docs_categoria.exists():
                documentos_agrupados[categoria] = docs_categoria
        
        # Documentos sem categoria
        docs_sem_categoria = documentos.filter(categoria__isnull=True)
        if docs_sem_categoria.exists():
            documentos_agrupados['Sem Categoria'] = docs_sem_categoria
    
    # Paginação para resultados de busca
    paginator = None
    page_obj = None
    if filtros_aplicados:
        paginator = Paginator(documentos, 12)  # 12 documentos por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    
    # Dados para os filtros
    todas_categorias = Categoria.objects.all()
    todas_tags = Tag.objects.all()
    
    # Tags selecionadas para o template
    tags_selecionadas = []
    if tags_ids:
        tags_selecionadas = Tag.objects.filter(id__in=tags_ids)
    
    context = {
        'documentos': documentos if filtros_aplicados else None,
        'documentos_agrupados': documentos_agrupados if not filtros_aplicados else None,
        'page_obj': page_obj,
        'todas_categorias': todas_categorias,
        'todas_tags': todas_tags,
        'query': query,
        'categoria_selecionada': categoria_id,
        'tags_selecionadas': tags_selecionadas,
        'filtros_aplicados': filtros_aplicados,
        'total_resultados': documentos.count() if filtros_aplicados else sum(len(docs) for docs in documentos_agrupados.values()),
    }
    
    return render(request, 'busca_docs/busca_documentos.html', context)


def detalhes_documento(request, documento_id):
    """
    View para exibir detalhes de um documento específico.
    """
    try:
        documento = Documento.objects.select_related('categoria').prefetch_related('tags').get(
            id=documento_id, 
            ativo=True
        )
    except Documento.DoesNotExist:
        from django.http import Http404
        raise Http404("Documento não encontrado")
    
    context = {
        'documento': documento,
    }
    
    return render(request, 'busca_docs/detalhes_documento.html', context)


def adicionar_documento(request):
    """
    View para adicionar um novo documento.
    """
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save()
            messages.success(
                request, 
                f'Documento "{documento.titulo}" foi adicionado com sucesso!'
            )
            return redirect('busca_docs:detalhes_documento', documento_id=documento.id)
        else:
            messages.error(
                request, 
                'Erro ao adicionar o documento. Verifique os dados e tente novamente.'
            )
    else:
        form = DocumentoForm()
    
    context = {
        'form': form,
        'todas_categorias': Categoria.objects.all().order_by('nome'),
        'todas_tags': Tag.objects.all().order_by('nome'),
    }
    
    return render(request, 'busca_docs/adicionar_documento.html', context)

