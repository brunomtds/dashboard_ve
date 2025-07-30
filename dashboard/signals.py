from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from .models import SolicitacaoAcesso, UserProfile

@receiver(post_save, sender=SolicitacaoAcesso)
def criar_usuario_quando_aprovado(sender, instance, created, **kwargs):
    if instance.aprovado:
        # Verifica se já existe um User com esse email
        if not User.objects.filter(email=instance.email).exists():
            # Cria username com o início do email
            username = instance.email.split('@')[0]

            # Garante que o username é único
            original_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            # Extrai primeiro nome
            primeiro_nome = instance.nome.split()[0]

            # Cria usuário
            user = User.objects.create_user(
                username=username,
                first_name=primeiro_nome,
                email=instance.email,
                password='VEJ@2025',
                is_staff=False,
                is_superuser=False
            )

            # Cria o perfil vinculado
            UserProfile.objects.create(
                user=user,
                ramal=instance.ramal,
                departamento=instance.departamento,
                first_access=True
            )

@receiver(user_logged_in)
def reset_first_access(sender, user, request, **kwargs):
    if hasattr(user, 'profile') and user.profile.first_access:
        if request.path == reverse('password_change_done'):
            user.profile.first_access = False
            user.profile.save()