from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView
from django.contrib.auth.models import User
from accounts.models import SolicitacaoAcesso, UserProfile
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST
from django.db.models import Q
from accounts.models import Departamento, SolicitacaoAcesso

# Esta função verifica se o usuário é um membro da equipe (staff)
def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff, login_url='/') # Redireciona para a home se não for staff
def adm_dashboard_view(request):
    """
    View principal do painel de administração customizado.
    """
    # Calcula as estatísticas
    usuarios_ativos_count = User.objects.filter(is_active=True).count() - 1  # Exclui o superusuário
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

class UserListView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'administracao/user_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20  # Mostra 20 usuários por página

    def test_func(self):
        # Garante que apenas usuários staff acessem esta página
        return self.request.user.is_staff

    def get_queryset(self):
        # Começamos com a query base, otimizada para evitar múltiplas buscas ao banco
        # Excluímos superusuários para não serem gerenciados por esta interface
        queryset = User.objects.filter(is_superuser=False).select_related(
            'profile__departamento'
        ).order_by('first_name', 'last_name')

        # Lógica de Busca
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(username__icontains=query)
            )

        # Lógica de Filtro por Departamento
        departamento_id = self.request.GET.get('departamento')
        if departamento_id:
            queryset = queryset.filter(profile__departamento__id=departamento_id)
        
        # Lógica de Filtro por Status
        status = self.request.GET.get('status')
        if status == 'ativo':
            queryset = queryset.filter(is_active=True)
        elif status == 'inativo':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        # Adicionamos dados extras ao contexto para os filtros no template
        context = super().get_context_data(**kwargs)
        context['departamentos'] = Departamento.objects.all()
        # Passamos os parâmetros de filtro atuais de volta para o template
        context['current_query'] = self.request.GET.get('q', '')
        context['current_departamento'] = self.request.GET.get('departamento', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context
    
@require_POST  # Garante que esta ação só pode ser feita via POST (segurança)
@user_passes_test(is_staff)
def toggle_user_active_status(request, pk):
    """
    Ativa ou desativa um usuário.
    """
    # Usamos get_object_or_404 para buscar o usuário ou retornar um erro 404 se não existir.
    # Excluímos superusuários para evitar que sejam desativados acidentalmente.
    user_to_toggle = get_object_or_404(User, pk=pk, is_superuser=False)

    # Inverte o status atual (se está ativo, desativa; se inativo, ativa)
    user_to_toggle.is_active = not user_to_toggle.is_active
    user_to_toggle.save(update_fields=['is_active'])

    # Cria uma mensagem de feedback para o administrador
    status = "ativado" if user_to_toggle.is_active else "desativado"
    messages.success(request, f"O usuário {user_to_toggle.username} foi {status} com sucesso.")

    # Redireciona de volta para a lista de usuários
    return redirect('administracao:user_list')

@require_POST
@user_passes_test(is_staff)
def force_password_change(request, pk):
    """
    Força um usuário a trocar sua senha no próximo login.
    """
    user_to_force = get_object_or_404(User, pk=pk, is_superuser=False)

    try:
        profile = user_to_force.profile
        profile.first_access = True
        profile.save(update_fields=['first_access'])
        messages.success(request, f"O usuário {user_to_force.username} será forçado a trocar a senha no próximo login.")
    except User.profile.RelatedObjectDoesNotExist:
        messages.error(request, f"O usuário {user_to_force.username} não possui um perfil associado para forçar a troca de senha.")

    return redirect('administracao:user_list')