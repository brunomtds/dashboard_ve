import locale
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from collections import defaultdict
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.views.decorators.http import require_POST

from .forms import EntidadeForm

# Isso garante que a formatação de datas, como nomes de meses, use o idioma correto.
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'portuguese') # Alternativa para Windows

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
    form_class = EntidadeForm
    template_name = 'controle_oficio/entidade_form.html'
    success_url = reverse_lazy('entidade_list')


class EntidadeUpdateView(UpdateView):
    model = Entidade
    form_class = EntidadeForm
    template_name = 'controle_oficio/entidade_form.html'
    success_url = reverse_lazy('entidade_list')


class EntidadeDetailView(DetailView):
    model = Entidade
    template_name = 'controle_oficio/entidade_detail.html'
    context_object_name = 'entidade'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 1. DADOS BASE ---
        fichas_entidade = self.object.fichas.all().order_by('numero')
        
        # --- 2. LÓGICA PARA ESTATÍSTICAS DE 30 DIAS ---
        data_limite = timezone.now() - timedelta(days=30)
        
        dnv_recent_use = fichas_entidade.filter(tipo='DNV', data_desfecho__gte=data_limite)
        context['dnv_30days_count'] = dnv_recent_use.count()

        do_recent_use = fichas_entidade.filter(tipo='DO', data_desfecho__gte=data_limite)
        context['do_30days_count'] = do_recent_use.count()

        # --- 3. LÓGICA DE AGRUPAMENTO OTIMIZADA (CORRIGIDA) ---
        # Busca todas as fichas disponíveis já com os dados do bloco (select_related).
        fichas_disponiveis = Ficha.objects.filter(status='Disponível').select_related('bloco').order_by('bloco__numero_inicial', 'numero')

        # Cria dicionários para agrupar as fichas por objeto de bloco.
        blocos_do_agrupados = {}
        blocos_dnv_agrupados = {}

        for ficha in fichas_disponiveis:
            if ficha.tipo == 'DO':
                if ficha.bloco not in blocos_do_agrupados:
                    blocos_do_agrupados[ficha.bloco] = []
                blocos_do_agrupados[ficha.bloco].append(ficha)
            elif ficha.tipo == 'DNV':
                if ficha.bloco not in blocos_dnv_agrupados:
                    blocos_dnv_agrupados[ficha.bloco] = []
                blocos_dnv_agrupados[ficha.bloco].append(ficha)

        # Transforma os dicionários na estrutura de lista que o template espera.
        grupos_do = []
        for bloco, fichas_do_bloco in blocos_do_agrupados.items():
            grupos_do.append({
                'bloco': bloco,
                'fichas_disponiveis': fichas_do_bloco,
                'ficha_ids': [f.id for f in fichas_do_bloco]
            })

        grupos_dnv = []
        for bloco, fichas_dnv_bloco in blocos_dnv_agrupados.items():
            grupos_dnv.append({
                'bloco': bloco,
                'fichas_disponiveis': fichas_dnv_bloco,
                'ficha_ids': [f.id for f in fichas_dnv_bloco]
            })
        
        context['grupos_do'] = grupos_do
        context['grupos_dnv'] = grupos_dnv

        # --- 4. DADOS PARA A LISTAGEM DE FICHAS DA ENTIDADE ---
        context['fichas_do_distribuidas'] = fichas_entidade.filter(tipo='DO', status='Distribuida')
        context['fichas_dnv_distribuidas'] = fichas_entidade.filter(tipo='DNV', status='Distribuida')
        context['fichas_do_distribuidas_ids'] = list(context['fichas_do_distribuidas'].values_list('id', flat=True))
        context['fichas_dnv_distribuidas_ids'] = list(context['fichas_dnv_distribuidas'].values_list('id', flat=True))
        
        context['fichas_do_finalizadas'] = fichas_entidade.filter(tipo='DO').exclude(status__in=['Distribuida', 'Disponível'])
        context['fichas_dnv_finalizadas'] = fichas_entidade.filter(tipo='DNV').exclude(status__in=['Distribuida', 'Disponível'])

        # --- 5. DADOS PARA O MODAL DE TRANSFERÊNCIA ---
        context['outras_entidades'] = Entidade.objects.exclude(pk=self.object.pk).order_by('nome')

        context['id_numero_map'] = {
            str(f.id): f.numero for f in fichas_disponiveis
        }
        
        return context

# =========================
# TRANSFERIR FICHAS EM LOTE
# =========================

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


def dashboard_view(request):
    selected_dates = request.GET.getlist('datas')
    base_queryset = Ficha.objects.all()

    if selected_dates:
        base_queryset = base_queryset.filter(data_recebimento__date__in=selected_dates)

    # --- Cálculo das Estatísticas (sem alteração) ---
    total_recebidas = base_queryset.count()
    disponiveis_count = base_queryset.filter(status='Disponível').count()
    distribuidas_count = base_queryset.filter(status='Distribuida').count()
    finalizadas_count = base_queryset.filter(status__in=['Utilizada', 'Cancelada']).count()
    
    if total_recebidas > 0:
        percentual_finalizadas = (finalizadas_count / total_recebidas) * 100
    else:
        percentual_finalizadas = 0

    # --- NOVA LÓGICA PARA AGRUPAR DATAS ---
    # 1. Busca todas as datas únicas de recebimento do banco
    all_unique_dates = Ficha.objects.dates('data_recebimento', 'day', order='DESC')

    # 2. Usa um dicionário para agrupar as datas por Mês/Ano
    dates_by_month = defaultdict(list)
    for date in all_unique_dates:
        # Cria uma chave única para cada mês/ano, ex: "Setembro 2025"
        month_key = date.strftime('%B de %Y').capitalize()
        dates_by_month[month_key].append(date)

    # 3. Transforma o dicionário na estrutura de lista que o template usará
    grouped_dates = []
    for month_year, dates in dates_by_month.items():
        grouped_dates.append({
            'month_year_display': month_year,
            'dates': dates
        })
    # --- FIM DA NOVA LÓGICA ---

    context = {
        'total_recebidas': total_recebidas,
        'disponiveis_count': disponiveis_count,
        'distribuidas_count': distribuidas_count,
        'percentual_finalizadas': percentual_finalizadas,
        'grouped_dates': grouped_dates, # Enviamos as datas agrupadas
        'selected_dates': selected_dates,
    }

    if 'HX-Request' in request.headers:
        return render(request, 'controle_oficio/partials/dashboard_stats.html', context)
    
    return render(request, 'controle_oficio/dashboard.html', context)