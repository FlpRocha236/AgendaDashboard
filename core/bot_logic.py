import yfinance as yf
from .models import Ativo, AnaliseBot

# --- LISTA DE ATIVOS PARA O RADAR (Você pode adicionar mais) ---
TICKERS_RADAR = [
    # Ações Fortes
    ('WEGE3.SA', 'ACAO'), ('PETR4.SA', 'ACAO'), ('VALE3.SA', 'ACAO'),
    ('BBAS3.SA', 'ACAO'), ('ITSA4.SA', 'ACAO'), ('MGLU3.SA', 'ACAO'),
    ('PSSA3.SA', 'ACAO'), ('EGIE3.SA', 'ACAO'), ('TAEE11.SA', 'ACAO'),
    # FIIs Populares
    ('MXRF11.SA', 'FII'), ('HGLG11.SA', 'FII'), ('XPLG11.SA', 'FII'),
    ('VISC11.SA', 'FII'), ('KNRI11.SA', 'FII'),
    # Cripto
    ('BTC-BRL', 'CRIPTO'), ('ETH-BRL', 'CRIPTO')
]

def calcular_fundamentos(ticker, tipo, info):
    """
    Função auxiliar que aplica a matemática de Graham/Bazin.
    Retorna um dicionário com os dados processados.
    """
    preco = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
    score = 0
    recomendacao = "NEUTRO"
    detalhes = {}

    if tipo == 'ACAO':
        pl = info.get('trailingPE', 0) or 0
        pvp = info.get('priceToBook', 0) or 0
        dy = (info.get('dividendYield', 0) or 0) * 100
        roe = (info.get('returnOnEquity', 0) or 0) * 100
        divida = info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0
        
        c_dy = dy >= 6.0
        c_pl = 0 < pl <= 15.0
        c_pvp = 0 < pvp <= 1.5
        c_roe = roe >= 10.0
        c_divida = divida <= 1.5
        
        score = sum([c_dy, c_pl, c_pvp, c_roe, c_divida])
        detalhes = {'pl': pl, 'pvp': pvp, 'dy': dy, 'roe': roe}

    elif tipo == 'FII':
        dy = (info.get('dividendYield', 0) or 0) * 100
        pvp = info.get('priceToBook', 0) or 0
        
        c_dy = dy >= 8.0
        c_pvp = 0.8 <= pvp <= 1.10
        
        if c_dy and c_pvp: score = 5
        elif c_dy: score = 3
        else: score = 1
        
        detalhes = {'dy': dy, 'pvp': pvp}

    elif tipo == 'CRIPTO':
        # Cripto no Radar é apenas informativo de preço, pois depende de % na carteira
        score = 3 
        recomendacao = "NEUTRO (Verificar % na Carteira)"
        detalhes = {}

    # Define Recomendação baseada no Score (Para Ações e FIIs)
    if tipo != 'CRIPTO':
        if score >= 4: recomendacao = "COMPRA FORTE"
        elif score == 3: recomendacao = "OBSERVAR"
        else: recomendacao = "AGUARDAR / CARO"

    return {
        'ticker': ticker.replace('.SA', '').replace('-BRL', ''),
        'tipo': tipo,
        'preco': preco,
        'score': score,
        'recomendacao': recomendacao,
        'detalhes': detalhes
    }

# --- FUNÇÃO 1: ANALISA SUA CARTEIRA (Já existente) ---
def executar_analise_carteira(user):
    ativos = Ativo.objects.filter(user=user)
    total_patrimonio = sum(a.total_investido() for a in ativos)
    
    for ativo in ativos:
        if ativo.tipo == 'CRIPTO': ticker_yf = f"{ativo.ticker}-BRL"
        elif ativo.ticker.endswith('.SA'): ticker_yf = ativo.ticker
        else: ticker_yf = f"{ativo.ticker}.SA"

        try:
            stock = yf.Ticker(ticker_yf)
            dados = calcular_fundamentos(ticker_yf, ativo.tipo, stock.info)
            
            # Sobrescreve lógica de Cripto para usar % da carteira
            if ativo.tipo == 'CRIPTO':
                percentual = (ativo.total_investido() / total_patrimonio * 100) if total_patrimonio > 0 else 0
                if percentual < 4: dados['score'], dados['recomendacao'] = 5, "COMPRAR (Abaixo da Meta)"
                elif percentual > 7: dados['score'], dados['recomendacao'] = 1, "VENDER (Acima da Meta)"
                else: dados['score'], dados['recomendacao'] = 3, "MANTER"

            # Salva no Banco
            AnaliseBot.objects.update_or_create(
                ativo=ativo,
                defaults={
                    'preco_atual': dados['preco'],
                    'recomendacao': dados['recomendacao'],
                    'pontuacao': dados['score'],
                    'pl': dados['detalhes'].get('pl', 0),
                    'pvp': dados['detalhes'].get('pvp', 0),
                    'dy': dados['detalhes'].get('dy', 0),
                    'roe': dados['detalhes'].get('roe', 0)
                }
            )
        except Exception as e:
            print(f"Erro {ativo.ticker}: {e}")

# --- FUNÇÃO 2: NOVO RADAR DE OPORTUNIDADES ---
def buscar_oportunidades_mercado():
    sugestoes = []
    
    for ticker, tipo in TICKERS_RADAR:
        try:
            stock = yf.Ticker(ticker)
            dados = calcular_fundamentos(ticker, tipo, stock.info)
            
            # Só adiciona na lista se for uma BOA oportunidade (Score >= 4)
            if dados['score'] >= 4:
                sugestoes.append(dados)
                
        except Exception as e:
            print(f"Erro Radar {ticker}: {e}")
            
    return sugestoes