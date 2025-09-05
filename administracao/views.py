from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView
from django.contrib.auth.models import User
from accounts.models import SolicitacaoAcesso, UserProfile
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

# Esta função verifica se o usuário é um membro da equipe (staff)
def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff, login_url='/') # Redireciona para a home se não for staff
def adm_dashboard_view(request):
    """
    View principal do painel de administração customizado.
    """
    # Calcula as estatísticas
    usuarios_ativos_count = User.objects.filter(is_active=True).count()
    solicitacoes_pendentes_count = SolicitacaoAcesso.objects.filter(aprovado=False).count()

    context = {
        'usuarios_ativos_count': usuarios_ativos_count,
        'solicitacoes_pendentes_count': solicitacoes_pendentes_count,
    }
    
    return render(request, 'administracao/dashboard.html', context)

class SolicitacaoListView(UserPassesTestMixin, ListView):
    model = SolicitacaoAcesso
    template_name = 'administracao/solicitacao_list.html'
    context_object_name = 'solicitacoes'

    def test_func(self):
        # Garante que apenas usuários staff acessem esta página
        return self.request.user.is_staff

    def get_queryset(self):
        # Sobrescrevemos o método padrão para buscar apenas as solicitações pendentes
        return SolicitacaoAcesso.objects.filter(aprovado=False).order_by('criado_em')

@require_POST  # Garante que esta ação só pode ser feita via POST
@user_passes_test(is_staff)
def aprovar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoAcesso, pk=pk)
    
    # Verifica novamente se o usuário já não existe
    if User.objects.filter(email=solicitacao.email).exists():
        messages.warning(request, f"Um usuário com o e-mail {solicitacao.email} já existe. A solicitação foi marcada como aprovada, mas nenhuma nova conta foi criada.")
    else:
        # Gera senha temporária
        allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        temp_password = get_random_string(12, allowed_chars)

        # Garante username único
        username = solicitacao.email.split('@')[0]
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        primeiro_nome = solicitacao.nome.split()[0]

        # Cria o usuário e seu perfil
        user = User.objects.create_user(
            username=username,
            first_name=primeiro_nome,
            email=solicitacao.email,
            password=temp_password
        )
        UserProfile.objects.create(
            user=user,
            ramal=solicitacao.ramal,
            departamento=solicitacao.departamento,
            first_access=True
        )
        messages.success(request, f"Usuário {username} criado com sucesso! A senha temporária é: {temp_password}")

    # Marca a solicitação como aprovada e a salva
    solicitacao.aprovado = True
    solicitacao.save()
    
    return redirect('administracao:solicitacao_list')


@require_POST
@user_passes_test(is_staff)
def rejeitar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoAcesso, pk=pk)
    nome_solicitante = solicitacao.nome
    solicitacao.delete()
    messages.info(request, f"A solicitação de {nome_solicitante} foi rejeitada e removida.")
    return redirect('administracao:solicitacao_list')