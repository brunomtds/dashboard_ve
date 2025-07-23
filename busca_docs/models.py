from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Tag(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Documento(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    arquivo = models.FileField(upload_to='documentos/')
    data_publicacao = models.DateField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-data_cadastro']

    def __str__(self):
        return self.titulo

