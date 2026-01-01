from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from datetime import datetime, timedelta
from .health_logic import gerar_diagnostico_financeiro
from .bot_logic import executar_analise_carteira, buscar_oportunidades_mercado

# Importação dos Models e Forms
from .models import (
    Compromisso, Nota, Transacao, CartaoCredito, DespesaCartao, 
    Ativo, OperacaoInvestimento, Desafio, SemanaDesafio, ContaPagar, 
    AnaliseBot  # <--- ADICIONADO AQUI
)
from .forms import (
    TransacaoForm, CompromissoForm, NotaForm, PerfilForm, CartaoForm, 
    DespesaCartaoForm, AtivoForm, OperacaoInvestimentoForm, DesafioForm, 
    UsuarioRegistroForm, ContaPagarForm
)

# Importação da Lógica do Robô
from .bot_logic import executar_analise_carteira  # <--- ADICIONADO AQUI

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

    # 5. CONTAS A PAGAR
    contas_pendentes = ContaPagar.objects.filter(user=request.user, pago=False).order_by('data_vencimento')

    context = {
        'receitas': receitas,
        'despesas': total_despesas,
        'saldo': saldo,
        'compromissos': proximos_compromissos,
        'notas': notas,
        'labels_invest': labels_invest,
        'data_invest': data_invest,
        'labels_cartao': labels_cartao,
        'data_cartao': data_cartao,
        'colors_cartao': colors_cartao,
        'desafio_ativo': desafio_ativo,
        'contas_pendentes': contas_pendentes, 
    }
    return render(request, 'dashboard.html', context)

# --- FINANÇAS (FLUXO E CARTÕES) ---
@login_required
def financas(request):
    # --- 1. CONFIGURAÇÃO DO FILTRO DE DATA ---
    agora = timezone.now()
    
    # Tenta pegar da URL (?mes=1&ano=2025), se não tiver, usa o atual
    mes_filtro = request.GET.get('mes', agora.month)
    ano_filtro = request.GET.get('ano', agora.year)
    
    try:
        mes_filtro = int(mes_filtro)
        ano_filtro = int(ano_filtro)
    except ValueError:
        mes_filtro = agora.month
        ano_filtro = agora.year

    # --- 2. FLUXO DE CAIXA (FILTRADO) ---
    transacoes = Transacao.objects.filter(
        user=request.user,
        data__month=mes_filtro,
        data__year=ano_filtro
    ).order_by('-data')

    # --- 3. CARTÕES DE CRÉDITO (PROJEÇÃO DA FATURA) ---
    cartoes = CartaoCredito.objects.filter(user=request.user)
    
    for cartao in cartoes:
        despesas = DespesaCartao.objects.filter(cartao=cartao)
        fatura_mes = 0 
        total_divida = 0 

        for despesa in despesas:
            total_divida += despesa.valor 

            # LÓGICA DE PROJEÇÃO:
            # Calcula a parcela baseada no Mês/Ano SELECIONADO pelo usuário
            valor_parcela = despesa.valor / despesa.parcelas
            
            # Quantos meses se passaram da compra até a data do filtro?
            meses_passados = (ano_filtro - despesa.data_compra.year) * 12 + (mes_filtro - despesa.data_compra.month)
            
            # Se o resultado estiver entre 0 e o número de parcelas, a conta cai neste mês filtrado
            if 0 <= meses_passados < despesa.parcelas:
                fatura_mes += valor_parcela
        
        cartao.fatura_atual = fatura_mes
        cartao.total_gasto = total_divida
        cartao.disponivel = cartao.limite - total_divida
        
        if cartao.limite > 0:
            cartao.porcentagem_uso = (total_divida / cartao.limite) * 100
        else:
            cartao.porcentagem_uso = 0

    context = {
        'transacoes': transacoes,
        'cartoes': cartoes,
        'mes_atual': mes_filtro,
        'ano_atual': ano_filtro,
    }
    return render(request, 'financas.html', context)

# --- INVESTIMENTOS & ROBÔ ---

@login_required
def investimentos_dashboard(request):
    ativos = Ativo.objects.filter(user=request.user)
    total_investido = sum(a.total_investido() for a in ativos)
    
    # Busca as análises salvas para exibir no Template
    analises = AnaliseBot.objects.filter(ativo__user=request.user).order_by('-pontuacao')

    context = {
        'ativos': ativos,
        'total_investido': total_investido,
        'analises': analises, 
    }
    return render(request, 'investimentos.html', context)

@login_required
def bot_executar(request):
    """ Botão que roda a análise """
    try:
        executar_analise_carteira(request.user)
        messages.success(request, "Robô finalizou a análise da carteira!")
    except Exception as e:
        messages.error(request, f"Erro ao rodar o robô: {str(e)}")
        
    return redirect('investimentos_dashboard')

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
            return redirect('investimentos_dashboard')
    else:
        form = AtivoForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Novo Ativo Financeiro'})

@login_required
def ativo_deletar(request, id):
    ativo = get_object_or_404(Ativo, pk=id)
    if ativo.user == request.user:
        ativo.delete()
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

            data_atual = desafio.data_inicio
            
            for i in range(1, desafio.duracao_semanas + 1):
                # LÓGICA DE DOBRA (Exponencial)
                # Fórmula: Valor Inicial * (2 elevado a (semana - 1))
                # i=1 -> 2^0 (1) -> Valor * 1
                # i=2 -> 2^1 (2) -> Valor * 2
                # i=3 -> 2^2 (4) -> Valor * 4
                
                fator_multiplicacao = 2 ** (i - 1)
                valor_semana = desafio.valor_inicial * fator_multiplicacao
                
                SemanaDesafio.objects.create(
                    desafio=desafio,
                    numero=i,
                    data_alvo=data_atual,
                    valor_meta=valor_semana,
                    depositado=False
                )
                
                data_atual = data_atual + timedelta(days=7)

            messages.success(request, 'Desafio Exponencial criado com sucesso!')
            return redirect('investimentos_dashboard')
    else:
        form = DesafioForm()
    
    return render(request, 'desafio_form.html', {'form': form})

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

# --- MÓDULO DE CONTAS A PAGAR (RECORRENTES) ---

@login_required
def conta_pagar_nova(request):
    if request.method == 'POST':
        form = ContaPagarForm(request.POST)
        if form.is_valid():
            conta = form.save(commit=False)
            conta.user = request.user
            conta.save()
            return redirect('dashboard')
    else:
        form = ContaPagarForm()
    return render(request, 'form_generico.html', {'form': form, 'titulo': 'Nova Conta / Alerta'})

@login_required
def conta_pagar_concluir(request, id):
    conta = get_object_or_404(ContaPagar, pk=id, user=request.user)
    
    # Marca como paga
    conta.pago = True
    conta.save()

    # Se for recorrente, cria a próxima automaticamente
    if conta.recorrencia in ['M', 'A']:
        nova_data = conta.data_vencimento
        
        if conta.recorrencia == 'M': # Mensal: Adiciona 1 mês
            mes = nova_data.month + 1
            ano = nova_data.year
            if mes > 12:
                mes = 1
                ano += 1
            
            try:
                nova_data = nova_data.replace(year=ano, month=mes)
            except ValueError:
                nova_data = nova_data.replace(year=ano, month=mes, day=28) 
                
        elif conta.recorrencia == 'A': # Anual: Adiciona 1 ano
            nova_data = nova_data.replace(year=nova_data.year + 1)

        # Cria a nova conta futura
        ContaPagar.objects.create(
            user=request.user,
            titulo=conta.titulo,
            valor=conta.valor,
            data_vencimento=nova_data,
            recorrencia=conta.recorrencia,
            pago=False
        )
        messages.success(request, 'Conta paga! A próxima fatura foi gerada automaticamente.')

    return redirect('dashboard')

@login_required
def conta_pagar_deletar(request, id):
    conta = get_object_or_404(ContaPagar, pk=id, user=request.user)
    conta.delete()
    return redirect('dashboard')

@login_required
def saude_financeira(request):
    diagnostico = gerar_diagnostico_financeiro(request.user)
    
    # Define cor do Score
    cor_score = 'success'
    msg_score = 'Excelente'
    if diagnostico['score'] < 50:
        cor_score = 'danger'
        msg_score = 'Crítico'
    elif diagnostico['score'] < 70:
        cor_score = 'warning'
        msg_score = 'Atenção'
        
    context = {
        'd': diagnostico,
        'cor_score': cor_score,
        'msg_score': msg_score
    }
    return render(request, 'saude_financeira.html', context)

@login_required
def radar_mercado(request):
    """
    Varre o mercado e retorna apenas as TOP oportunidades
    """
    oportunidades = buscar_oportunidades_mercado()
    
    context = {
        'oportunidades': oportunidades
    }
    return render(request, 'radar_mercado.html', context)