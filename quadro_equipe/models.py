from django.db import models
from django.core.exceptions import ValidationError


class Responsabilidade(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()

    class Meta:
        verbose_name = 'Responsabilidade'
        verbose_name_plural = 'Responsabilidades'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Funcionario(models.Model):
    nome = models.CharField(max_length=200)
    departamento = models.ForeignKey(
        'Departamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='funcionarios'
    )
    ramal = models.CharField(max_length=4)
    responsabilidades = models.ManyToManyField(
        Responsabilidade,
        related_name='funcionarios',
        blank=True
    )
    is_chefia = models.BooleanField(
        verbose_name='É Chefia?',
        default=False,
        help_text='Marque se este funcionário pode ser selecionado como chefia.'
    )

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Departamento(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    chefe = models.OneToOneField(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departamento_chefia'
    )

    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if self.chefe and not self.chefe.is_chefia:
            raise ValidationError({'chefe': 'Este funcionário não está marcado como chefia.'})

    def save(self, *args, **kwargs):
        self.full_clean()  # Garante que o clean() é executado mesmo em save direto
        super().save(*args, **kwargs)
