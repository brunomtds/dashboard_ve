from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


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
    context_object_name = 'entidade'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        fichas_entidade = self.object.fichas.all().order_by('numero')

        # Separa fichas por tipo E por status
        context['fichas_do_distribuidas'] = fichas_entidade.filter(tipo='DO', status='Distribuida')
        context['fichas_dnv_distribuidas'] = fichas_entidade.filter(tipo='DNV', status='Distribuida')
        context['fichas_do_distribuidas_ids'] = list(context['fichas_do_distribuidas'].values_list('id', flat=True))
        context['fichas_dnv_distribuidas_ids'] = list(context['fichas_dnv_distribuidas'].values_list('id', flat=True))

        # Lógica de fichas finalizadas (para a lista expansível)
        context['fichas_do_finalizadas'] = fichas_entidade.filter(tipo='DO').exclude(status='Distribuida')
        context['fichas_dnv_finalizadas'] = fichas_entidade.filter(tipo='DNV').exclude(status='Distribuida')


        # LÓGICA NOVA PARA A ESTATÍSTICA DE 30 DIAS 
        data_limite = timezone.now() - timedelta(days=30)
        
        # Filtra fichas DNV/DO utilizadas/canceladas nos últimos 30 dias
        dnv_recent_use = fichas_entidade.filter(
            tipo='DNV',
            data_desfecho__gte=data_limite  # __gte significa "maior ou igual a"
        )
        context['dnv_30days_count'] = dnv_recent_use.count()

        do_recent_use = fichas_entidade.filter(
            tipo='DO',
            data_desfecho__gte=data_limite  # __gte significa "maior ou igual a"
        )
        context['do_30days_count'] = do_recent_use.count()

        # Fichas disponíveis para distribuição
        context['fichas_disponiveis'] = Ficha.objects.filter(
            status='Disponível'
        ).order_by('numero')

        # Outras entidades (para o dropdown de transferência)
        context['outras_entidades'] = Entidade.objects.exclude(pk=self.object.pk).order_by('nome')
        
        return context

# =========================
# TRANSFERIR FICHAS EM LOTE
# =========================
@login_required
@require_POST
def transferir_fichas_em_lote(request):
    """
    Transfere múltiplas fichas de uma entidade para outra.
    """
    ficha_ids = request.POST.getlist('ficha_ids')
    nova_entidade_id = request.POST.get('nova_entidade_id')
    entidade_origem_id = request.POST.get('entidade_origem_id')

    if not ficha_ids or not nova_entidade_id:
        messages.warning(request, "Informações insuficientes para realizar a transferência.")
        return redirect('entidade_detail', pk=entidade_origem_id)

    try:
        nova_entidade = Entidade.objects.get(pk=nova_entidade_id)

        with transaction.atomic():
            fichas_para_transferir = Ficha.objects.filter(
                id__in=ficha_ids,
                entidade_id=entidade_origem_id # Garante que só estamos transferindo fichas da entidade correta
            )
            contagem = fichas_para_transferir.count()

            # .update() para uma única query no banco, muito mais rápido.
            fichas_para_transferir.update(
                entidade=nova_entidade,
                data_entrega=timezone.now() # Atualiza a data para a da nova entrega/transferência
            )

        messages.success(request, f"{contagem} fichas foram transferidas com sucesso para {nova_entidade.nome}.")
    except Entidade.DoesNotExist:
        messages.error(request, "A entidade de destino não foi encontrada.")
    except Exception as e:
        messages.error(request, f"Ocorreu um erro ao processar a transferência: {e}")

    return redirect('entidade_detail', pk=entidade_origem_id)

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contagens para as estatísticas
        blocos = self.get_queryset()
        context['total_blocos'] = blocos.count()
        context['blocos_do_count'] = blocos.filter(tipo='DO').count()
        context['blocos_dnv_count'] = blocos.filter(tipo='DNV').count()
        context['total_fichas'] = blocos.count() * 30  # Cada bloco tem 30 fichas
        
        # Adicionar contagens de fichas por status para cada bloco
        for bloco in context['blocos']:
            bloco.fichas_disponiveis_count = bloco.fichas.filter(status='Disponível').count()
            bloco.fichas_distribuidas_count = bloco.fichas.filter(status='Distribuida').count()
        
        return context

class BlocoDetailView(DetailView):
    model = Bloco
    template_name = 'controle_oficio/bloco_detail.html'
    context_object_name = 'bloco'


@login_required
@require_POST # Garante que esta view só aceita requisições POST
def dar_desfecho_ficha(request, ficha_id):
    """
    Atualiza o status de uma ficha para 'Utilizada' ou 'Cancelada'.
    """
    ficha = get_object_or_404(Ficha, pk=ficha_id)
    # Guarda o ID da entidade para redirecionar de volta para a página correta.
    entidade_id = ficha.entidade.id 

    novo_status = request.POST.get('status')

    # Validação para garantir que o status enviado é válido
    if novo_status not in ['Utilizada', 'Cancelada']:
        messages.error(request, "Status inválido para o desfecho.")
        return redirect('entidade_detail', pk=entidade_id)

    # Validação para garantir que a ficha está no estado correto para ser finalizada
    if ficha.status != 'Distribuida':
        messages.warning(request, f"A ficha {ficha.numero} não está com o status 'Distribuida' e não pode ser finalizada.")
        return redirect('entidade_detail', pk=entidade_id)

    # Se tudo estiver OK, atualiza os campos da ficha
    ficha.status = novo_status
    ficha.desfecho_por = request.user
    ficha.data_desfecho=timezone.now()
    # O método save() do model já cuida de preencher a data_desfecho
    ficha.save(update_fields=['status', 'desfecho_por', 'data_desfecho'])

    messages.success(request, f"A ficha {ficha.numero} foi marcada como '{novo_status}'.")
    return redirect('entidade_detail', pk=entidade_id)

@login_required
@require_POST
def dar_desfecho_em_lote(request):
    """
    Atualiza o status de múltiplas fichas de uma só vez.
    """
    ficha_ids = request.POST.getlist('ficha_ids')
    novo_status = request.POST.get('status')
    entidade_id = request.POST.get('entidade_id') # Precisamos saber para onde voltar

    if not ficha_ids:
        messages.warning(request, "Nenhuma ficha foi selecionada.")
        return redirect('entidade_detail', pk=entidade_id)

    if novo_status not in ['Utilizada', 'Cancelada']:
        messages.error(request, "Status inválido para o desfecho.")
        return redirect('entidade_detail', pk=entidade_id)

    try:
        with transaction.atomic():
            # Filtra apenas as fichas que pertencem à entidade e estão com status 'Distribuida'
            fichas_para_atualizar = Ficha.objects.filter(
                id__in=ficha_ids,
                entidade_id=entidade_id,
                status='Distribuida'
            )
            
            contagem = fichas_para_atualizar.count()

            # Usamos .update() para uma única query no banco, muito mais rápido.
            # Nota: .update() não chama o método .save() do model, 
            # então temos que setar a data_desfecho manualmente aqui.
            fichas_para_atualizar.update(
                status=novo_status,
                desfecho_por=request.user,
                data_desfecho=timezone.now()
            )

        messages.success(request, f"{contagem} fichas foram marcadas como '{novo_status}'.")
    except Exception as e:
        messages.error(request, f"Ocorreu um erro ao processar o lote: {e}")

    return redirect('entidade_detail', pk=entidade_id)
