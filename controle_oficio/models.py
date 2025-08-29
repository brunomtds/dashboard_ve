from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class Bloco(models.Model):
    TIPO_CHOICES = [
        ('DO', 'Declaração de Óbito'),
        ('DNV', 'Declaração de Nascido Vivo'),
    ]

    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES)

    numero_validator = RegexValidator(
        regex=r'^\d{8,10}$',
        message='Digite apenas números, entre 8 e 10 dígitos.'
    )

    numero_inicial = models.CharField(
        max_length=10,
        validators=[numero_validator],
        unique=True
    )
    data_recebimento = models.DateTimeField(default=timezone.now)

    def gerar_fichas(self):
        fichas_a_criar = []
        tamanho = 8 if self.tipo == 'DO' else 10  # tamanho fixo por tipo
        for i in range(30):
            numero_ficha = str(int(self.numero_inicial) + i).zfill(tamanho)
            fichas_a_criar.append(
                Ficha(
                    numero=numero_ficha,
                    bloco=self,
                    tipo=self.tipo,
                    data_recebimento=self.data_recebimento
                )
            )
        Ficha.objects.bulk_create(fichas_a_criar)


class Ficha(models.Model):
    STATUS_CHOICES = [
        ('Disponível', 'Disponível'),
        ('Distribuida', 'Distribuída'),
        ('Utilizada', 'Utilizada'),
        ('Cancelada', 'Cancelada'),
        ('Verificar', 'Verificar'),
    ]

    numero = models.CharField(max_length=10, unique=True)
    bloco = models.ForeignKey('Bloco', on_delete=models.CASCADE, related_name='fichas')
    tipo = models.CharField(
        max_length=3,
        choices=[('DO', 'Declaração de Óbito'), ('DNV', 'Declaração de Nascido Vivo')]
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Disponível')
    entidade = models.ForeignKey('Entidade', null=True, blank=True, on_delete=models.SET_NULL, related_name='fichas')
    data_recebimento = models.DateTimeField(default=timezone.now)
    data_entrega = models.DateTimeField(null=True, blank=True)
    data_desfecho = models.DateTimeField(null=True, blank=True)
    desfecho_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['numero']

    def save(self, *args, **kwargs):
        # Checar alteração de status
        if self.pk:
            old = Ficha.objects.get(pk=self.pk)
            if old.status != self.status and self.status in ['Utilizada', 'Cancelada']:
                self.data_desfecho = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ficha {self.numero} - {self.get_tipo_display()}"


# Signal para criar as fichas automaticamente ao salvar um novo bloco
@receiver(post_save, sender=Bloco)
def criar_fichas_apos_bloco(sender, instance, created, **kwargs):
    if created:
        instance.gerar_fichas()

class Entidade(models.Model):
    TIPO_CHOICES = [
        ('Medico', 'Médico'),
        ('Estabelecimento', 'Estabelecimento de Saúde'),
        ('Parteiro', 'Parteiro(a)'),
        ('Enfermeiro', 'Enfermeiro(a)'),
        ('IML', 'Instituto Médico Legal'),
    ]

    TIPO_DOC_CHOICES = [
        ('CPF', 'CPF'),
        ('CNES', 'CNES'),
        ('RG', 'RG'),
        ('COREN', 'Coren'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    tipo_documento = models.CharField(max_length=10, choices=TIPO_DOC_CHOICES)
    numero_documento = models.CharField(max_length=20, unique=True)  # CNES ou outro número identificador
    nome = models.CharField(max_length=255)
    responsavel_tecnico = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"