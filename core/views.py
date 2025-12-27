from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from datetime import datetime, timedelta

# Importação dos Models e Forms
from .models import Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, Ativo, OperacaoInvestimento, Desafio, SemanaDesafio
from .forms import TransacaoForm, CompromissoForm, NotaForm, PerfilForm, CartaoForm, DespesaCartaoForm, AtivoForm, OperacaoInvestimentoForm, DesafioForm, UsuarioRegistroForm

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

# --- DASHBOARD PRINCIPAL ---

@login_required
def dashboard(request):
    agora = timezone.now()
    mes_atual = agora.month
    ano_atual = agora.year

    # 1. DADOS FINANCEIROS BÁSICOS (Fluxo de Caixa)
    receitas = Transacao.objects.filter(user=request.user, tipo='receita').aggregate(Sum('valor'))['valor__sum'] or 0
    despesas_caixa = Transacao.objects.filter(user=request.user, tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or 0
    
    # --- CÁLCULO DA FATURA TOTAL DOS CARTÕES (PARA SOMAR NAS DESPESAS) ---
    fatura_total_cartoes = 0
    cartoes = CartaoCredito.objects.filter(user=request.user)
    
    # Listas para o Gráfico de Cartões
    labels_cartao = []
    data_cartao = []
    colors_cartao = []

    for cartao in cartoes:
        despesas = DespesaCartao.objects.filter(cartao=cartao)
        fatura_deste_cartao = 0
        limite_tomado = 0

        for despesa in despesas:
            limite_tomado += despesa.valor # Total da dívida para cor da barra

            # Lógica da Parcela Mensal
            valor_parcela = despesa.valor / despesa.parcelas
            meses_passados = (ano_atual - despesa.data_compra.year) * 12 + (mes_atual - despesa.data_compra.month)
            
            if 0 <= meses_passados < despesa.parcelas:
                fatura_deste_cartao += valor_parcela

        # Soma ao total geral de despesas
        fatura_total_cartoes += fatura_deste_cartao
        
        # Prepara dados para o Gráfico
        labels_cartao.append(cartao.nome)
        data_cartao.append(float(fatura_deste_cartao)) # <--- Agora exibe a Fatura, não o Total
        
        # Define a cor baseada no LIMITE (ainda é útil ver se o cartão está estourado)
        uso = (limite_tomado / cartao.limite) * 100 if cartao.limite > 0 else 0
        if uso > 80:
            colors_cartao.append('#e74a3b') # Vermelho
        elif uso > 50:
            colors_cartao.append('#f6c23e') # Amarelo
        else:
            colors_cartao.append('#4e73df') # Azul

    # O "Despesas Mês" agora é: Gastos em Dinheiro + Fatura dos Cartões
    total_despesas = despesas_caixa + fatura_total_cartoes
    saldo = receitas - total_despesas

    # 2. DADOS PARA O GRÁFICO DE APORTES (INVESTIMENTOS)
    data_limite = agora.date() - timedelta(days=180)
    aportes = OperacaoInvestimento.objects.filter(
        ativo__user=request.user, 
        tipo='C', 
        data__gte=data_limite
    ).order_by('data')

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

    # 3. AGENDA E NOTAS
    proximos_compromissos = Compromisso.objects.filter(
        user=request.user, data_hora__gte=agora, concluido=False
    ).order_by('data_hora')[:3]
    notas = Nota.objects.filter(user=request.user).order_by('-atualizado_em')[:2]

    # 4. DESAFIO ATIVO
    desafio_ativo = Desafio.objects.filter(user=request.user, concluido=False).first()

    context = {
        'receitas': receitas,
        'despesas': total_despesas, # <--- Agora inclui os cartões!
        'saldo': saldo,
        'compromissos': proximos_compromissos,
        'notas': notas,
        'labels_invest': labels_invest,
        'data_invest': data_invest,
        'labels_cartao': labels_cartao,
        'data_cartao': data_cartao,
        'colors_cartao': colors_cartao,
        'desafio_ativo': desafio_ativo,
    }
    return render(request, 'dashboard.html', context)

# --- FINANÇAS (FLUXO E CARTÕES) ---

@login_required
def financas(request):
    # 1. Fluxo de Caixa (Transações normais)
    transacoes = Transacao.objects.filter(user=request.user).order_by('-data')

    # 2. Cartões de Crédito (Lógica da Fatura Mensal)
    cartoes = CartaoCredito.objects.filter(user=request.user)
    
    agora = timezone.now()
    mes_atual = agora.month
    ano_atual = agora.year

    for cartao in cartoes:
        despesas = DespesaCartao.objects.filter(cartao=cartao)
        fatura_mes = 0 # Valor que será pago neste mês
        total_divida = 0 # Valor total comprometido (limite usado)

        for despesa in despesas:
            # Calcula o valor total usado do limite
            total_divida += despesa.valor 

            # --- LÓGICA DA PARCELA MENSAL ---
            # 1. Qual o valor da parcela?
            valor_parcela = despesa.valor / despesa.parcelas
            
            # 2. Calcular quantos meses se passaram desde a compra até hoje
            # Ex: Comprou em Janeiro, estamos em Março = passaram 2 meses
            meses_passados = (ano_atual - despesa.data_compra.year) * 12 + (mes_atual - despesa.data_compra.month)
            
            # 3. Ajuste do Dia de Fechamento (Opcional, mas preciso)
            # Se a compra foi feita DEPOIS do fechamento, ela pula pro próximo mês
            # Vamos simplificar: Se meses_passados for menor que o total de parcelas, a conta existe.
            if 0 <= meses_passados < despesa.parcelas:
                fatura_mes += valor_parcela
        
        # Atribui os valores calculados ao objeto cartão para usar no HTML
        cartao.fatura_atual = fatura_mes
        cartao.total_gasto = total_divida # Limite tomado total
        cartao.disponivel = cartao.limite - total_divida
        
        # Barra de progresso (baseada no limite total tomado)
        if cartao.limite > 0:
            cartao.porcentagem_uso = (total_divida / cartao.limite) * 100
        else:
            cartao.porcentagem_uso = 0

    context = {
        'transacoes': transacoes,
        'cartoes': cartoes,
    }
    return render(request, 'financas.html', context)

@login_required
def investimentos_dashboard(request):
    ativos = Ativo.objects.filter(user=request.user)
    total_investido = sum(a.total_investido() for a in ativos)
    
    context = {
        'ativos': ativos,
        'total_investido': total_investido,
    }
    return render(request, 'investimentos.html', context)

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

@login_required
def compromisso_concluir(request, id):
    comp = get_object_or_404(Compromisso, pk=id, user=request.user)
    comp.concluido = not comp.concluido 
    comp.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

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
def cartao_deletar(request, id):
    cartao = get_object_or_404(CartaoCredito, pk=id)
    if cartao.user == request.user:
        cartao.delete()
    return redirect('financas')

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
            # AGORA REDIRECIONA PARA INVESTIMENTOS
            return redirect('investimentos_dashboard')
    else:
        form = AtivoForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Novo Ativo Financeiro'})

@login_required
def ativo_deletar(request, id):
    ativo = get_object_or_404(Ativo, pk=id)
    if ativo.user == request.user:
        ativo.delete()
    # AGORA REDIRECIONA PARA INVESTIMENTOS
    return redirect('investimentos_dashboard')

@login_required
def operacao_nova(request):
    if request.method == 'POST':
        form = OperacaoInvestimentoForm(request.POST)
        if form.is_valid():
            operacao = form.save(commit=False)
            
            if operacao.ativo.user != request.user:
                return redirect('investimentos_dashboard')
            
            operacao.save()
            recalcular_ativo(operacao.ativo)
            
            # AGORA REDIRECIONA PARA INVESTIMENTOS
            return redirect('investimentos_dashboard')
    else:
        form = OperacaoInvestimentoForm()
        form.fields['ativo'].queryset = Ativo.objects.filter(user=request.user)

    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Operação (Aporte/Venda)'})

@login_required
def operacao_editar(request, id):
    operacao = get_object_or_404(OperacaoInvestimento, pk=id)
    if operacao.ativo.user != request.user: return redirect('investimentos_dashboard')

    if request.method == 'POST':
        form = OperacaoInvestimentoForm(request.POST, instance=operacao)
        if form.is_valid():
            operacao = form.save()
            recalcular_ativo(operacao.ativo) 
            # AGORA REDIRECIONA PARA INVESTIMENTOS
            return redirect('investimentos_dashboard')
    else:
        form = OperacaoInvestimentoForm(instance=operacao)
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Editar Operação'})

@login_required
def operacao_deletar(request, id):
    operacao = get_object_or_404(OperacaoInvestimento, pk=id)
    ativo = operacao.ativo
    if ativo.user == request.user:
        operacao.delete()
        recalcular_ativo(ativo) 
    # AGORA REDIRECIONA PARA INVESTIMENTOS
    return redirect('investimentos_dashboard')

# --- MÓDULO DE DESAFIOS & METAS ---

@login_required
def desafios_lista(request):
    desafios = Desafio.objects.filter(user=request.user, concluido=False)
    return render(request, 'desafios.html', {'desafios': desafios})

@login_required
def desafio_novo(request):
    if request.method == 'POST':
        form = DesafioForm(request.POST)
        if form.is_valid():
            desafio = form.save(commit=False)
            desafio.user = request.user
            desafio.save()

            valor_atual = desafio.valor_inicial
            data_atual = desafio.data_inicio
            
            for i in range(1, desafio.duracao_semanas + 1):
                SemanaDesafio.objects.create(
                    desafio=desafio,
                    numero=i,
                    data_prevista=data_atual,
                    valor=valor_atual
                )
                valor_atual += desafio.incremento
                data_atual += timedelta(days=7)

            return redirect('desafios_lista')
    else:
        form = DesafioForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Novo Desafio Financeiro'})

@login_required
def desafio_pagar_semana(request, id):
    semana = get_object_or_404(SemanaDesafio, pk=id)
    if semana.desafio.user == request.user:
        semana.pago = not semana.pago 
        semana.data_pagamento = timezone.now() if semana.pago else None
        semana.save()
    return redirect('desafios_lista')

@login_required
def desafio_excluir(request, id):
    desafio = get_object_or_404(Desafio, pk=id)
    if desafio.user == request.user:
        desafio.delete()
    return redirect('desafios_lista')

# --- CADASTRO DE USUÁRIOS ---

def registrar_usuario(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta criada com sucesso! Faça login.')
            return redirect('login')
    else:
        form = UsuarioRegistroForm()
    return render(request, 'registration/register.html', {'form': form})