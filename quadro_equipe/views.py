from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator

from .models import Funcionario, Departamento, Responsabilidade
from .forms import FuncionarioForm, ResponsabilidadeForm


def quadro_funcionarios(request):
    query = request.GET.get('q', '').strip()
    departamento_id = request.GET.get('departamento', '')
    so_chefias = request.GET.get('so_chefias', '')

    funcionarios = Funcionario.objects.select_related('departamento').prefetch_related('responsabilidades').all()

    if query:
        funcionarios = funcionarios.filter(nome__icontains=query)

    if departamento_id:
        try:
            departamento_id = int(departamento_id)
            funcionarios = funcionarios.filter(departamento_id=departamento_id)
        except (ValueError, TypeError):
            pass

    if so_chefias:
        funcionarios = funcionarios.filter(is_chefia=True)

    funcionarios = funcionarios.order_by('nome')

    paginator = Paginator(funcionarios, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'funcionarios': page_obj,
        'departamentos': Departamento.objects.all().order_by('nome'),
        'query': query,
        'departamento_id': departamento_id,
        'so_chefias': so_chefias,
        'total_resultados': funcionarios.count(),
        'page_obj': page_obj,
    }

    return render(request, 'quadro_equipe/quadro_funcionarios.html', context)


def adicionar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            funcionario = form.save()
            messages.success(request, f'Funcionário "{funcionario.nome}" adicionado com sucesso.')
            return redirect('quadro_equipe:quadro_funcionarios')
        else:
            messages.error(request, 'Erro ao salvar funcionário. Verifique os dados.')
    else:
        form = FuncionarioForm()

    context = {'form': form}

    return render(request, 'quadro_equipe/adicionar_funcionario.html', context)


def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Funcionário "{funcionario.nome}" atualizado com sucesso.')
            return redirect('quadro_equipe:quadro_funcionarios')
        else:
            messages.error(request, 'Erro ao atualizar funcionário.')
    else:
        form = FuncionarioForm(instance=funcionario)

    context = {
        'form': form,
        'funcionario': funcionario
    }

    return render(request, 'quadro_equipe/editar_funcionario.html', context)


def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    if request.method == 'POST':
        funcionario.delete()
        messages.success(request, f'Funcionário "{funcionario.nome}" excluído com sucesso.')
        return redirect('quadro_equipe:quadro_funcionarios')

    context = {
        'funcionario': funcionario
    }

    return render(request, 'quadro_equipe/excluir_funcionario.html', context)


def adicionar_responsabilidade(request):
    if request.method == 'POST':
        form = ResponsabilidadeForm(request.POST)
        if form.is_valid():
            responsabilidade = form.save()
            messages.success(request, f'Responsabilidade "{responsabilidade.nome}" adicionada com sucesso.')
            return redirect('quadro_equipe:quadro_funcionarios')
        else:
            messages.error(request, 'Erro ao salvar responsabilidade.')
    else:
        form = ResponsabilidadeForm()

    context = {'form': form}

    return render(request, 'quadro_equipe/adicionar_responsabilidade.html', context)
