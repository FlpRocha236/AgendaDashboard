from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Transacao, ContaPagar, CartaoCredito, AnaliseBot, Ativo

def gerar_diagnostico_financeiro(user):
    # --- 1. COLETA DE DADOS (Últimos 30 dias) ---
    hoje = timezone.now().date()
    inicio_mes = hoje - timedelta(days=30)
    
    # Fluxo de Caixa
    receitas = Transacao.objects.filter(user=user, tipo='receita', data__gte=inicio_mes).aggregate(Sum('valor'))['valor__sum'] or 0
    despesas = Transacao.objects.filter(user=user, tipo='despesa', data__gte=inicio_mes).aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Contas e Dívidas
    contas_atrasadas = ContaPagar.objects.filter(user=user, pago=False, data_vencimento__lt=hoje)
    total_atrasado = sum(c.valor for c in contas_atrasadas)
    qtd_atrasadas = contas_atrasadas.count()
    
    # Cartão de Crédito (Limite tomado)
    cartoes = CartaoCredito.objects.filter(user=user)
    limite_total = sum(c.limite for c in cartoes)
    divida_cartao = 0
    for c in cartoes:
        gastos = c.despesas.aggregate(Sum('valor'))['valor__sum'] or 0
        divida_cartao += gastos

    # Investimentos (Qualidade da Carteira via Robô)
    ativos = Ativo.objects.filter(user=user)
    analises_ruins = AnaliseBot.objects.filter(ativo__user=user, recomendacao__icontains='VENDER')
    analises_boas = AnaliseBot.objects.filter(ativo__user=user, recomendacao__icontains='COMPRAR')
    total_investido = sum(a.total_investido() for a in ativos)

    # --- 2. CÁLCULO DO SCORE (0 a 100) ---
    score = 50 # Começa na média
    
    # Critério 1: Fluxo de Caixa (+30 pts)
    saldo = receitas - despesas
    if receitas > 0:
        taxa_poupanca = ((receitas - despesas) / receitas) * 100
    else:
        taxa_poupanca = 0
        
    if taxa_poupanca >= 20: score += 30 # Excelente
    elif taxa_poupanca > 0: score += 15 # Ok
    else: score -= 20 # Gastando mais que ganha (Perigo!)

    # Critério 2: Inadimplência (-30 pts)
    if qtd_atrasadas > 0: score -= 30
    else: score += 10

    # Critério 3: Alavancagem no Cartão (-20 pts)
    uso_cartao = (divida_cartao / limite_total * 100) if limite_total > 0 else 0
    if uso_cartao > 70: score -= 20
    elif uso_cartao > 30: score -= 5
    else: score += 10 # Uso saudável

    # Ajuste final (Min 0, Max 100)
    score = max(0, min(100, score))

    # --- 3. GERAR RECOMENDAÇÕES (TEXTO) ---
    recomendacoes = []
    
    # Sobre Fluxo
    if saldo < 0:
        recomendacoes.append({
            'tipo': 'danger', 
            'titulo': 'Alerta Vermelho no Caixa',
            'msg': f'Você gastou R$ {abs(saldo):.2f} a mais do que ganhou nos últimos 30 dias. Corte gastos supérfluos imediatamente.'
        })
    elif taxa_poupanca < 20:
        recomendacoes.append({
            'tipo': 'warning',
            'titulo': 'Aumente seus Aportes',
            'msg': f'Sua taxa de poupança é de {taxa_poupanca:.1f}%. O ideal para liberdade financeira é acima de 20%.'
        })
    else:
        recomendacoes.append({
            'tipo': 'success',
            'titulo': 'Fluxo Excelente',
            'msg': 'Parabéns! Você está poupando uma grande parte da sua renda. Mantenha assim.'
        })

    # Sobre Dívidas
    if qtd_atrasadas > 0:
        recomendacoes.append({
            'tipo': 'danger',
            'titulo': 'Contas Atrasadas',
            'msg': f'Você tem {qtd_atrasadas} contas vencidas totalizando R$ {total_atrasado:.2f}. Pague isso antes de investir!'
        })
    
    if uso_cartao > 70:
        recomendacoes.append({
            'tipo': 'warning',
            'titulo': 'Cuidado com o Cartão',
            'msg': 'Você já usou mais de 70% do seu limite total. O risco de bola de neve é alto.'
        })

    # Sobre Investimentos
    if analises_ruins.exists():
        nomes = ", ".join([a.ativo.ticker for a in analises_ruins])
        recomendacoes.append({
            'tipo': 'info',
            'titulo': 'Otimização de Carteira',
            'msg': f'O Robô identificou ativos com fundamentos ruins na sua carteira: {nomes}. Considere vender.'
        })
    
    if total_investido == 0 and saldo > 0:
        recomendacoes.append({
            'tipo': 'primary',
            'titulo': 'Comece a Investir',
            'msg': 'Você tem saldo positivo mas nenhum investimento cadastrado. Crie sua reserva de emergência.'
        })

    return {
        'score': score,
        'taxa_poupanca': taxa_poupanca,
        'total_atrasado': total_atrasado,
        'uso_cartao': uso_cartao,
        'recomendacoes': recomendacoes
    }