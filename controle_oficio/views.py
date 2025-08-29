from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import Bloco, Entidade, Ficha


# =========================
# BLOCO
# =========================
class BlocoCreateView(CreateView):
    model = Bloco
    fields = ['tipo', 'numero_inicial']
    template_name = 'controle_oficio/bloco_form.html'
    success_url = reverse_lazy('bloco_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # As fichas já são geradas pelo signal post_save
        return response


# =========================
# ENTIDADE
# =========================
class EntidadeListView(ListView):
    model = Entidade
    template_name = 'controle_oficio/entidade_list.html'


class EntidadeCreateView(CreateView):
    model = Entidade
    fields = ['tipo', 'tipo_documento', 'numero_documento', 'nome', 'responsavel_tecnico']
    template_name = 'controle_oficio/entidade_form.html'
    success_url = reverse_lazy('entidade_list')


class EntidadeUpdateView(UpdateView):
    model = Entidade
    fields = ['tipo', 'tipo_documento', 'numero_documento', 'nome', 'responsavel_tecnico']
    template_name = 'controle_oficio/entidade_form.html'
    success_url = reverse_lazy('entidade_list')


class EntidadeDetailView(DetailView):
    model = Entidade
    template_name = 'controle_oficio/entidade_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entidade = self.object
        
        # Busca todas as fichas em uma única query
        todas_fichas = entidade.fichas.all()
        
        # Divide em DO e DNV em Python
        context['fichas_do'] = [f for f in todas_fichas if f.tipo == 'DO']
        context['fichas_dnv'] = [f for f in todas_fichas if f.tipo == 'DNV']
        
        return context


# =========================
# DISTRIBUIR FICHAS
# =========================
def distribuir_fichas(request, entidade_id):
    entidade = get_object_or_404(Entidade, pk=entidade_id)

    if request.method == 'POST':
        numeros_selecionados = request.POST.getlist('fichas')

        if not numeros_selecionados:
            messages.warning(request, "Nenhuma ficha foi selecionada para distribuição.")
            return redirect('entidade_detail', pk=entidade.id)

        # Separação de feedback
        numeros_invalidos = []
        numeros_indisponiveis = []
        numeros_distribuidos = []

        with transaction.atomic():
            # Lock pessimista para evitar corrida
            fichas_tentadas = (
                Ficha.objects
                .select_for_update()
                .filter(numero__in=numeros_selecionados)
            )

            # Mapear os números realmente encontrados no banco
            encontrados = {f.numero: f for f in fichas_tentadas}

            for numero in numeros_selecionados:
                ficha = encontrados.get(numero)
                if not ficha:
                    numeros_invalidos.append(numero)
                elif ficha.status != 'Disponível':
                    numeros_indisponiveis.append(numero)
                else:
                    ficha.entidade = entidade
                    ficha.status = 'Distribuida'
                    ficha.data_entrega = timezone.now()
                    ficha.save(update_fields=['entidade', 'status', 'data_entrega'])
                    numeros_distribuidos.append(numero)

        # Mensagens de retorno
        if numeros_distribuidos:
            messages.success(
                request,
                f"{len(numeros_distribuidos)} fichas distribuídas para {entidade.nome}: "
                f"{', '.join(numeros_distribuidos)}."
            )

        if numeros_indisponiveis:
            messages.warning(
                request,
                f"{len(numeros_indisponiveis)} fichas já estavam indisponíveis: "
                f"{', '.join(numeros_indisponiveis)}."
            )

        if numeros_invalidos:
            messages.error(
                request,
                f"{len(numeros_invalidos)} fichas não existem no sistema: "
                f"{', '.join(numeros_invalidos)}."
            )

        return redirect('entidade_detail', pk=entidade.id)

class BlocoListView(ListView):
    model = Bloco
    template_name = 'controle_oficio/bloco_list.html'
    context_object_name = 'blocos'
    ordering = ['-data_recebimento']  # ou por número inicial, se preferir

class BlocoDetailView(DetailView):
    model = Bloco
    template_name = 'controle_oficio/bloco_detail.html'
    context_object_name = 'bloco'