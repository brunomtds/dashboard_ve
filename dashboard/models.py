from django.db import models
from quadro_equipe.models import Departamento

class SolicitacaoAcesso(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    ramal = models.CharField(max_length=4, blank=True, null=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)
    aprovado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.email})"