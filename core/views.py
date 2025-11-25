from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Compromisso, Nota, Transacao
from django.shortcuts import redirect, get_object_or_404
from .forms import TransacaoForm, CompromissoForm, NotaForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import PerfilForm

@login_required
def dashboard(request):
    # 1. Lógica Financeira (Soma tudo que é receita e tudo que é despesa)
    receitas = Transacao.objects.filter(user=request.user, tipo='receita').aggregate(Sum('valor'))['valor__sum'] or 0
    despesas = Transacao.objects.filter(user=request.user, tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo = receitas - despesas

    # 2. Lógica da Agenda (Pega os próximos 5 compromissos que ainda não passaram)
    agora = timezone.now()
    proximos_compromissos = Compromisso.objects.filter(
        user=request.user, 
        data_hora__gte=agora, 
        concluido=False
    ).order_by('data_hora')[:5]

    # 3. Lógica das Notas (Pega as últimas 3 criadas)
    notas = Nota.objects.filter(user=request.user).order_by('-atualizado_em')[:3]

    context = {
        'receitas': receitas,
        'despesas': despesas,
        'saldo': saldo,
        'compromissos': proximos_compromissos,
        'notas': notas
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def financas(request):
    transacoes = Transacao.objects.filter(user=request.user).order_by('-data')
    return render(request, 'financas.html', {'transacoes': transacoes})

@login_required
def agenda(request):
    compromissos = Compromisso.objects.filter(user=request.user).order_by('data_hora')
    return render(request, 'agenda.html', {'compromissos': compromissos})

@login_required
def notas(request):
    todas_notas = Nota.objects.filter(user=request.user).order_by('-atualizado_em')
    return render(request, 'notas.html', {'notas': todas_notas})

# --- TRANSAÇÕES ---
@login_required
def transacao_nova(request):
    if request.method == 'POST':
        form = TransacaoForm(request.POST)
        if form.is_valid():
            transacao = form.save(commit=False)
            transacao.user = request.user # Associa ao usuário logado
            transacao.save()
            return redirect('financas')
    else:
        form = TransacaoForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Transação'})

@login_required
def transacao_editar(request, id):
    transacao = get_object_or_404(Transacao, pk=id, user=request.user)
    if request.method == 'POST':
        form = TransacaoForm(request.POST, instance=transacao)
        if form.is_valid():
            form.save()
            return redirect('financas')
    else:
        form = TransacaoForm(instance=transacao)
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Editar Transação'})

@login_required
def transacao_deletar(request, id):
    transacao = get_object_or_404(Transacao, pk=id, user=request.user)
    transacao.delete()
    return redirect('financas')

# --- AGENDA ---
@login_required
def agenda_nova(request):
    if request.method == 'POST':
        form = CompromissoForm(request.POST)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.user = request.user
            comp.save()
            return redirect('agenda')
    else:
        form = CompromissoForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Novo Compromisso'})

@login_required
def agenda_editar(request, id):
    comp = get_object_or_404(Compromisso, pk=id, user=request.user)
    if request.method == 'POST':
        form = CompromissoForm(request.POST, instance=comp)
        if form.is_valid():
            form.save()
            return redirect('agenda')
    else:
        form = CompromissoForm(instance=comp)
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Editar Compromisso'})

@login_required
def agenda_deletar(request, id):
    comp = get_object_or_404(Compromisso, pk=id, user=request.user)
    comp.delete()
    return redirect('agenda')

# --- NOTAS ---
@login_required
def nota_nova(request):
    if request.method == 'POST':
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.user = request.user
            nota.save()
            return redirect('notas')
    else:
        form = NotaForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Nota'})

@login_required
def nota_editar(request, id):
    nota = get_object_or_404(Nota, pk=id, user=request.user)
    if request.method == 'POST':
        form = NotaForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            return redirect('notas')
    else:
        form = NotaForm(instance=nota)
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Editar Nota'})

@login_required
def nota_deletar(request, id):
    nota = get_object_or_404(Nota, pk=id, user=request.user)
    nota.delete()
    return redirect('notas')

# --- CONFIGURAÇÕES ---

@login_required
def configuracoes(request):
    # Processa o formulário de dados pessoais
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seus dados foram atualizados com sucesso!')
            return redirect('configuracoes')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'configuracoes.html', {'form': form})

@login_required
def alterar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Importante: mantém o usuário logado após trocar a senha
            update_session_auth_hash(request, user) 
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('configuracoes')
    else:
        form = PasswordChangeForm(request.user)
        
        # Hackzinho para aplicar a classe Bootstrap nos campos desse form padrão do Django
        for field in form.fields.values():
            field.widget.attrs['class'] = 'form-control'

    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Alterar Senha'})