from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from datetime import datetime, timedelta

# Importação dos Models e Forms
from .models import Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, Ativo, OperacaoInvestimento
from .forms import TransacaoForm, CompromissoForm, NotaForm, PerfilForm, CartaoForm, DespesaCartaoForm, AtivoForm, OperacaoInvestimentoForm

# --- FUNÇÃO AUXILIAR (Helper) ---
def recalcular_ativo(ativo):
    """
    Recalcula a quantidade e preço médio do ativo baseada em todas as operações.
    Chamada sempre que se cria, edita ou exclui uma operação.
    """
    compras = OperacaoInvestimento.objects.filter(ativo=ativo, tipo='C').aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    vendas = OperacaoInvestimento.objects.filter(ativo=ativo, tipo='V').aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    ativo.quantidade_atual = compras - vendas
    
    if ativo.quantidade_atual > 0:
        total_gasto = 0
        todas_compras = OperacaoInvestimento.objects.filter(ativo=ativo, tipo='C')
        for c in todas_compras:
            # Soma: (Qtd * Preço) + Taxas
            total_gasto += (c.quantidade * c.preco_unitario) + c.taxas
        
        # Preço Médio Simples = Total Gasto / Total de Cotas Compradas
        ativo.preco_medio = total_gasto / compras
    else:
        ativo.preco_medio = 0
    ativo.save()

# --- DASHBOARD & FINANÇAS ---

@login_required
def dashboard(request):
    # 1. DADOS FINANCEIROS BÁSICOS (KPIs)
    receitas = Transacao.objects.filter(user=request.user, tipo='receita').aggregate(Sum('valor'))['valor__sum'] or 0
    despesas = Transacao.objects.filter(user=request.user, tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo = receitas - despesas

    # 2. DADOS PARA O GRÁFICO DE APORTES (INVESTIMENTOS)
    data_limite = timezone.now().date() - timedelta(days=180) # Últimos 6 meses
    
    aportes = OperacaoInvestimento.objects.filter(
        ativo__user=request.user, 
        tipo='C', 
        data__gte=data_limite
    ).order_by('data')

    # Agrupando por mês
    aportes_mes = {}
    for aporte in aportes:
        mes_ano = aporte.data.strftime("%b/%y")
        valor = (aporte.quantidade * aporte.preco_unitario) + aporte.taxas
        
        if mes_ano in aportes_mes:
            aportes_mes[mes_ano] += float(valor)
        else:
            aportes_mes[mes_ano] = float(valor)

    labels_invest = list(aportes_mes.keys())
    data_invest = list(aportes_mes.values())

    # 3. DADOS PARA O GRÁFICO DE CARTÕES
    cartoes = CartaoCredito.objects.filter(user=request.user)
    labels_cartao = []
    data_cartao = []
    colors_cartao = []

    for cartao in cartoes:
        gasto = DespesaCartao.objects.filter(cartao=cartao).aggregate(Sum('valor'))['valor__sum'] or 0
        
        labels_cartao.append(cartao.nome)
        data_cartao.append(float(gasto))
        
        # Define cor baseada no uso do limite
        uso = (gasto / cartao.limite) * 100 if cartao.limite > 0 else 0
        if uso > 80:
            colors_cartao.append('#e74a3b') # Vermelho
        elif uso > 50:
            colors_cartao.append('#f6c23e') # Amarelo
        else:
            colors_cartao.append('#4e73df') # Azul

    # 4. AGENDA E NOTAS
    agora = timezone.now()
    proximos_compromissos = Compromisso.objects.filter(
        user=request.user, data_hora__gte=agora, concluido=False
    ).order_by('data_hora')[:3]
    
    notas = Nota.objects.filter(user=request.user).order_by('-atualizado_em')[:2]

    context = {
        'receitas': receitas,
        'despesas': despesas,
        'saldo': saldo,
        'compromissos': proximos_compromissos,
        'notas': notas,
        'labels_invest': labels_invest,
        'data_invest': data_invest,
        'labels_cartao': labels_cartao,
        'data_cartao': data_cartao,
        'colors_cartao': colors_cartao,
    }
    return render(request, 'dashboard.html', context)

@login_required
def financas(request):
    # 1. Fluxo de Caixa
    transacoes = Transacao.objects.filter(user=request.user).order_by('-data')

    # 2. Cartões de Crédito
    cartoes = CartaoCredito.objects.filter(user=request.user)
    for cartao in cartoes:
        total_gasto = DespesaCartao.objects.filter(cartao=cartao).aggregate(Sum('valor'))['valor__sum'] or 0
        cartao.total_gasto = total_gasto
        cartao.disponivel = cartao.limite - total_gasto
        
        if cartao.limite > 0:
            cartao.porcentagem_uso = (total_gasto / cartao.limite) * 100
        else:
            cartao.porcentagem_uso = 0

    # 3. Investimentos
    ativos = Ativo.objects.filter(user=request.user)
    total_investido = sum(a.total_investido() for a in ativos)

    context = {
        'transacoes': transacoes,
        'cartoes': cartoes,
        'ativos': ativos,
        'total_investido': total_investido
    }
    return render(request, 'financas.html', context)

# --- AGENDA & NOTAS (Listas) ---

@login_required
def agenda(request):
    compromissos = Compromisso.objects.filter(user=request.user).order_by('data_hora')
    return render(request, 'agenda.html', {'compromissos': compromissos})

@login_required
def notas(request):
    todas_notas = Nota.objects.filter(user=request.user).order_by('-atualizado_em')
    return render(request, 'notas.html', {'notas': todas_notas})

# --- CRUD TRANSAÇÕES (CAIXA) ---

@login_required
def transacao_nova(request):
    if request.method == 'POST':
        form = TransacaoForm(request.POST)
        if form.is_valid():
            transacao = form.save(commit=False)
            transacao.user = request.user
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

# --- CRUD AGENDA ---

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

# --- CRUD NOTAS ---

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

# --- CONFIGURAÇÕES DO USUÁRIO ---

@login_required
def configuracoes(request):
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
            update_session_auth_hash(request, user) 
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('configuracoes')
    else:
        form = PasswordChangeForm(request.user)
        for field in form.fields.values():
            field.widget.attrs['class'] = 'form-control'
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Alterar Senha'})

# --- CRUD CARTÕES E DESPESAS ---

@login_required
def cartao_novo(request):
    if request.method == 'POST':
        form = CartaoForm(request.POST)
        if form.is_valid():
            cartao = form.save(commit=False)
            cartao.user = request.user
            cartao.save()
            return redirect('financas')
    else:
        form = CartaoForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Novo Cartão de Crédito'})

@login_required
def despesa_cartao_nova(request):
    if request.method == 'POST':
        form = DespesaCartaoForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('financas')
    else:
        form = DespesaCartaoForm()
        form.fields['cartao'].queryset = CartaoCredito.objects.filter(user=request.user)
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Despesa no Cartão'})

@login_required
def despesa_cartao_editar(request, id):
    despesa = get_object_or_404(DespesaCartao, pk=id)
    if despesa.cartao.user != request.user: return redirect('financas') # Segurança

    if request.method == 'POST':
        form = DespesaCartaoForm(request.POST, instance=despesa)
        if form.is_valid():
            form.save()
            return redirect('financas')
    else:
        form = DespesaCartaoForm(instance=despesa)
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Editar Despesa'})

@login_required
def despesa_cartao_deletar(request, id):
    despesa = get_object_or_404(DespesaCartao, pk=id)
    if despesa.cartao.user == request.user:
        despesa.delete()
    return redirect('financas')

# --- CRUD INVESTIMENTOS ---

@login_required
def ativo_novo(request):
    if request.method == 'POST':
        form = AtivoForm(request.POST)
        if form.is_valid():
            ativo = form.save(commit=False)
            ativo.user = request.user
            ativo.save()
            return redirect('financas')
    else:
        form = AtivoForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Novo Ativo Financeiro'})

@login_required
def operacao_nova(request):
    if request.method == 'POST':
        form = OperacaoInvestimentoForm(request.POST)
        if form.is_valid():
            operacao = form.save(commit=False)
            
            # Segurança: verificar se o ativo pertence ao usuário
            if operacao.ativo.user != request.user:
                return redirect('financas')
            
            operacao.save()
            recalcular_ativo(operacao.ativo) # <--- Uso da função auxiliar

            return redirect('financas')
    else:
        form = OperacaoInvestimentoForm()
        form.fields['ativo'].queryset = Ativo.objects.filter(user=request.user)

    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Operação (Aporte/Venda)'})

@login_required
def operacao_editar(request, id):
    operacao = get_object_or_404(OperacaoInvestimento, pk=id)
    if operacao.ativo.user != request.user: return redirect('financas')

    if request.method == 'POST':
        form = OperacaoInvestimentoForm(request.POST, instance=operacao)
        if form.is_valid():
            operacao = form.save()
            recalcular_ativo(operacao.ativo) # Recalcula saldo após editar
            return redirect('financas')
    else:
        form = OperacaoInvestimentoForm(instance=operacao)
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Editar Operação'})

@login_required
def operacao_deletar(request, id):
    operacao = get_object_or_404(OperacaoInvestimento, pk=id)
    ativo = operacao.ativo
    if ativo.user == request.user:
        operacao.delete()
        recalcular_ativo(ativo) # Recalcula saldo após deletar
    return redirect('financas')

# --- ADICIONE NO FINAL DO ARQUIVO ---

@login_required
def cartao_deletar(request, id):
    cartao = get_object_or_404(CartaoCredito, pk=id)
    # Segurança: Só deleta se o cartão for do usuário logado
    if cartao.user == request.user:
        cartao.delete()
    return redirect('financas')

@login_required
def ativo_deletar(request, id):
    ativo = get_object_or_404(Ativo, pk=id)
    # Segurança: Só deleta se o ativo for do usuário logado
    if ativo.user == request.user:
        ativo.delete()
    return redirect('financas')