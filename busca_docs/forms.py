from django import forms
from .models import Categoria, Tag, Documento


class BuscaDocumentosForm(forms.Form):
    """
    Formulário para busca avançada de documentos.
    """
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite palavras-chave para buscar...',
            'class': 'mt-1 block w-full max-w-md p-2 border rounded-md'
        }),
        label='Busca por título ou descrição'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=True,
        empty_label="Todas as categorias",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full p-2 border rounded-md'
        }),
        label='Categoria'
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300'
        }),
        label='Tags'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar as opções
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        self.fields['tags'].queryset = Tag.objects.all().order_by('nome')


class DocumentoForm(forms.ModelForm):
    """
    Formulário para criação e edição de documentos.
    """
    class Meta:
        model = Documento
        fields = ['titulo', 'descricao', 'categoria', 'arquivo', 'data_publicacao', 'tags']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md',
                'placeholder': 'Digite o título do documento'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md',
                'rows': 4,
                'placeholder': 'Descrição detalhada do documento (opcional)'
            }),
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md'
            }),
            'arquivo': forms.FileInput(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md',
                'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'
            }),
            'data_publicacao': forms.DateInput(attrs={
                'class': 'mt-1 block w-full p-2 border rounded-md',
                'type': 'date'
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'rounded border-gray-300'
            }),
        }
        labels = {
            'titulo': 'Título do Documento',
            'descricao': 'Descrição',
            'categoria': 'Categoria',
            'arquivo': 'Arquivo',
            'data_publicacao': 'Data de Publicação',
            'tags': 'Tags',
        }
        help_texts = {
            'titulo': 'Nome do documento que aparecerá na busca',
            'descricao': 'Descrição detalhada para facilitar a busca',
            'categoria': 'Selecione uma categoria para organizar o documento',
            'arquivo': 'Formatos aceitos: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG',
            'data_publicacao': 'Data de publicação do documento (opcional)',
            'tags': 'Selecione tags para facilitar a busca',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar as opções
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        self.fields['tags'].queryset = Tag.objects.all().order_by('nome')
        
        # Tornar categoria opcional
        self.fields['categoria'].empty_label = "Selecione uma categoria"
        
        # Configurar campo de tags
        self.fields['tags'].required = False

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if titulo:
            titulo = titulo.strip()
            if len(titulo) < 3:
                raise forms.ValidationError('O título deve ter pelo menos 3 caracteres.')
        return titulo

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo:
            # Verificar tamanho do arquivo (máximo 10MB)
            if arquivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('O arquivo deve ter no máximo 10MB.')
            
            # Verificar extensão do arquivo
            extensoes_permitidas = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
            nome_arquivo = arquivo.name.lower()
            if not any(nome_arquivo.endswith(ext) for ext in extensoes_permitidas):
                raise forms.ValidationError('Formato de arquivo não permitido. Use: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG.')
        
        return arquivo

