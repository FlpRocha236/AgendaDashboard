from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.utils import timezone
from .models import Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, Ativo, OperacaoInvestimento
from django.shortcuts import redirect, get_object_or_404
from .forms import TransacaoForm, CompromissoForm, NotaForm, PerfilForm, CartaoForm, DespesaCartaoForm, AtivoForm, OperacaoInvestimentoForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models.functions import TruncMonth

@login_required
def dashboard(request):
    # 1. DADOS FINANCEIROS BÁSICOS (KPIs)
    receitas = Transacao.objects.filter(user=request.user, tipo='receita').aggregate(Sum('valor'))['valor__sum'] or 0
    despesas = Transacao.objects.filter(user=request.user, tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo = receitas - despesas

    # 2. DADOS PARA O GRÁFICO DE APORTES (INVESTIMENTOS)
    from datetime import datetime, timedelta
    
    data_limite = timezone.now().date() - timedelta(days=180) # Últimos 6 meses
    
    # --- A CORREÇÃO ESTÁ AQUI EMBAIXO ---
    aportes = OperacaoInvestimento.objects.filter(
        ativo__user=request.user, # <--- CORRIGIDO: Era user__user, agora é ativo__user
        tipo='C', 
        data__gte=data_limite
    ).order_by('data')

    # Agrupando por mês (ex: "Jan/25": 500.00)
    aportes_mes = {}
    for aporte in aportes:
        mes_ano = aporte.data.strftime("%b/%y") # Ex: "Nov/25"
        valor = (aporte.quantidade * aporte.preco_unitario) + aporte.taxas
        
        if mes_ano in aportes_mes:
            aportes_mes[mes_ano] += float(valor)
        else:
            aportes_mes[mes_ano] = float(valor)

    # Listas para o Chart.js
    labels_invest = list(aportes_mes.keys())
    data_invest = list(aportes_mes.values())

    # 3. DADOS PARA O GRÁFICO DE CARTÕES
    cartoes = CartaoCredito.objects.filter(user=request.user)
    labels_cartao = []
    data_cartao = []
    colors_cartao = []

    for cartao in cartoes:
        # Calcula gasto atual
        gasto = DespesaCartao.objects.filter(cartao=cartao).aggregate(Sum('valor'))['valor__sum'] or 0
        
        labels_cartao.append(cartao.nome)
        data_cartao.append(float(gasto))
        
        # Define cor baseada no uso do limite (Visual Alert)
        uso = (gasto / cartao.limite) * 100 if cartao.limite > 0 else 0
        if uso > 80:
            colors_cartao.append('#e74a3b') # Vermelho (Perigo)
        elif uso > 50:
            colors_cartao.append('#f6c23e') # Amarelo (Atenção)
        else:
            colors_cartao.append('#4e73df') # Azul (Ok)

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
    # 1. Fluxo de Caixa (Mantém o que já existia)
    transacoes = Transacao.objects.filter(user=request.user).order_by('-data')

    # 2. Cartões de Crédito
    cartoes = CartaoCredito.objects.filter(user=request.user)
    for cartao in cartoes:
        # Calcula o total gasto no cartão (simplificado para o total geral por enquanto)
        total_gasto = DespesaCartao.objects.filter(cartao=cartao).aggregate(Sum('valor'))['valor__sum'] or 0
        cartao.total_gasto = total_gasto
        cartao.disponivel = cartao.limite - total_gasto
        # Calcula porcentagem de uso para a barra de progresso
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

# CRUD CARTÕES

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
            # Aqui poderíamos adicionar lógica para verificar se o cartão pertence ao user
            form.save() 
            return redirect('financas')
    else:
        form = DespesaCartaoForm()
        # Filtra para aparecer apenas os cartões do usuário logado no dropdown
        form.fields['cartao'].queryset = CartaoCredito.objects.filter(user=request.user)
        
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Despesa no Cartão'})

# CRUD INVESTIMENTOS

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
                return redirect('financas') # Bloqueia se tentar mexer no ativo de outro
            
            operacao.save()

            # --- LÓGICA MÁGICA: ATUALIZA O SALDO DO ATIVO ---
            ativo = operacao.ativo
            
            # 1. Recalcula Quantidade
            # Soma todas as compras e subtrai todas as vendas
            compras = OperacaoInvestimento.objects.filter(ativo=ativo, tipo='C').aggregate(Sum('quantidade'))['quantidade__sum'] or 0
            vendas = OperacaoInvestimento.objects.filter(ativo=ativo, tipo='V').aggregate(Sum('quantidade'))['quantidade__sum'] or 0
            ativo.quantidade_atual = compras - vendas
            
            # 2. Recalcula Preço Médio (Média Ponderada simples das compras)
            # Nota: Isso é uma simplificação. PM fiscal é mais complexo, mas serve para gestão pessoal.
            if ativo.quantidade_atual > 0:
                total_gasto = 0
                todas_compras = OperacaoInvestimento.objects.filter(ativo=ativo, tipo='C')
                for c in todas_compras:
                    total_gasto += (c.quantidade * c.preco_unitario) + c.taxas
                
                # Se só comprou, o PM é o total gasto / total comprado
                # Se vendeu, a lógica contábil mantém o PM, mas vamos simplificar:
                ativo.preco_medio = total_gasto / compras
            else:
                ativo.preco_medio = 0

            ativo.save()
            # -----------------------------------------------

            return redirect('financas')
    else:
        form = OperacaoInvestimentoForm()
        # Filtra o dropdown para mostrar apenas ativos do usuário logado
        form.fields['ativo'].queryset = Ativo.objects.filter(user=request.user)

    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Operação (Aporte/Venda)'})