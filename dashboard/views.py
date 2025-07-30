from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from .models import SolicitacaoAcesso 
from quadro_equipe.models import Departamento

@login_required
def dashboard_view(request):
    return render(request, 'dashboard/index.html')


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

class CustomPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Marca como primeiro acesso concluído
        if hasattr(self.request.user, 'profile'):
            self.request.user.profile.first_access = False
            self.request.user.profile.save()

        return response