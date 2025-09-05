from django.shortcuts import render, redirect
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from .models import SolicitacaoAcesso, Departamento
from django.contrib.auth.views import LoginView

# Create your views here.
def solicitar_acesso(request):
    departamentos = Departamento.objects.all()
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == "POST":
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        ramal = request.POST.get('ramal')
        departamento_id = request.POST.get('departamento')

        if not SolicitacaoAcesso.objects.filter(email=email).exists():
            try:
                departamento = Departamento.objects.get(id=departamento_id)
                SolicitacaoAcesso.objects.create(
                    nome=nome,
                    email=email,
                    ramal=ramal,
                    departamento=departamento
                )
                return render(request, 'registration/access_solicitation.html', {
                    'success': True,
                    'departamentos': departamentos
                })
            except Departamento.DoesNotExist:
                return render(request, 'registration/access_solicitation.html', {
                    'error': 'Departamento inválido.',
                    'departamentos': departamentos
                })
        else:
            return render(request, 'registration/access_solicitation.html', {
                'error': 'Já existe uma solicitação com esse e-mail.',
                'departamentos': departamentos
            })

    return render(request, 'registration/access_solicitation.html', {
        'departamentos': departamentos
    })

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        # Esta função é chamada DEPOIS que o Django confirma que o login e a senha estão corretos.
        # Primeiro, deixamos o Django fazer o login do usuário.
        response = super().form_valid(form)

        # Agora, com o usuário já logado (self.request.user), verificamos o perfil.
        try:
            if self.request.user.profile.first_access:
                # Se for o primeiro acesso, ignoramos o redirecionamento padrão
                # e forçamos o usuário a ir para a página de troca de senha.
                return redirect('accounts:password_change')
        except AttributeError:
            # Se o usuário não tiver perfil, apenas continua o fluxo normal.
            pass

        # Se não for o primeiro acesso, o usuário segue o fluxo normal de redirecionamento.
        return response


class CustomPasswordChangeView(PasswordChangeView):
    # Define para onde o usuário será redirecionado APÓS trocar a senha com sucesso
    success_url = reverse_lazy('accounts:password_change_done')
    
    # Define qual template será usado para mostrar o formulário
    template_name = 'registration/password_change_form.html'

    def form_valid(self, form):
        # Primeiro, o Django executa a troca de senha padrão
        response = super().form_valid(form)

        # DEPOIS, nosso código customizado é executado:
        try:
            profile = self.request.user.profile
            # A flag é desativada aqui!
            profile.first_access = False
            profile.save()
        except AttributeError:
            # Ignora silenciosamente se o usuário (ex: superuser) não tiver perfil
            pass
        
        return response

