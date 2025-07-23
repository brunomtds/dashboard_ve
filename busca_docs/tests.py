from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Categoria, Tag, Documento


class BuscaDocsTestCase(TestCase):
    """
    Testes para o app de busca de documentos.
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes.
        """
        self.client = Client()
        
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Criar dados de teste
        self.categoria = Categoria.objects.create(nome='Categoria Teste')
        self.tag1 = Tag.objects.create(nome='Tag1')
        self.tag2 = Tag.objects.create(nome='Tag2')
        
        self.documento = Documento.objects.create(
            titulo='Documento Teste',
            descricao='Descrição do documento de teste',
            categoria=self.categoria,
            ativo=True
        )
        self.documento.tags.add(self.tag1, self.tag2)
    
    def test_busca_documentos_view(self):
        """
        Testa se a view principal de busca está funcionando.
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('busca_docs:busca_documentos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buscar Documentos')
        self.assertContains(response, self.documento.titulo)
    
    def test_busca_por_texto(self):
        """
        Testa a busca por texto livre.
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('busca_docs:busca_documentos'),
            {'q': 'Documento'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.documento.titulo)
    
    def test_filtro_por_categoria(self):
        """
        Testa o filtro por categoria.
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('busca_docs:busca_documentos'),
            {'categoria': self.categoria.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.documento.titulo)
    
    def test_filtro_por_tags(self):
        """
        Testa o filtro por tags.
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('busca_docs:busca_documentos'),
            {'tags': [self.tag1.id]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.documento.titulo)
    
    def test_detalhes_documento_view(self):
        """
        Testa a view de detalhes do documento.
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('busca_docs:detalhes_documento', args=[self.documento.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.documento.titulo)
        self.assertContains(response, self.documento.descricao)
    
    def test_documento_inativo_nao_aparece(self):
        """
        Testa se documentos inativos não aparecem na busca.
        """
        self.documento.ativo = False
        self.documento.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('busca_docs:busca_documentos'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.documento.titulo)

