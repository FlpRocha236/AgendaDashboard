import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from django.utils import timezone
from .models import Ativo, AnaliseBot

# --- 1. CONFIGURAÇÃO DE DISFARCE (Apenas para o Fundamentus) ---
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

# --- 2. FUNÇÃO DE ANÁLISE DA CARTEIRA (CORRIGIDA) ---
def executar_analise_carteira(user):
    ativos = Ativo.objects.filter(user=user)
    
    # REMOVI A SESSÃO AQUI. O yfinance vai gerenciar a dele sozinho.
    
    print("--- INICIANDO ANÁLISE COMPLETA (LOCAL) ---")

    for ativo in ativos:
        # Prepara ticker para o Yahoo
        if ativo.tipo == 'CRIPTO': ticker_yf = f"{ativo.ticker}-BRL"
        elif ativo.ticker.endswith('.SA'): ticker_yf = ativo.ticker
        else: ticker_yf = f"{ativo.ticker}.SA"

        try:
            # --- MUDANÇA AQUI: Não passamos mais session=session ---
            stock = yf.Ticker(ticker_yf) 
            
            # A) PREÇO ATUAL (Prioriza fast_info)
            try:
                preco_atual = stock.fast_info['last_price']
            except:
                try:
                    info = stock.info
                    preco_atual = info.get('currentPrice') or info.get('regularMarketPrice') or 0
                except:
                    print(f"Erro ao pegar preço de {ativo.ticker}")
                    continue

            if preco_atual and preco_atual > 0:
                # --- CÁLCULO 1: VARIAÇÃO DE COTA ---
                ativo.preco_medio = float(ativo.preco_medio)
                ativo.quantidade_atual = float(ativo.quantidade_atual)
                preco_atual_float = float(preco_atual)

                variacao_unitaria = preco_atual_float - ativo.preco_medio
                ativo.valorizacao_rs = variacao_unitaria * ativo.quantidade_atual
                
                if ativo.preco_medio > 0:
                    ativo.valorizacao_pct = ((preco_atual_float / ativo.preco_medio) - 1) * 100
                else:
                    ativo.valorizacao_pct = 0

                # --- CÁLCULO 2: DIVIDENDOS ACUMULADOS ---
                try:
                    if ativo.tipo in ['ACAO', 'FII']:
                        divs = stock.dividends
                        
                        if not divs.empty:
                            # Converte data do banco para UTC
                            data_inicio = pd.Timestamp(ativo.data_inicio).tz_localize('UTC')
                            divs_filtrados = divs[divs.index >= data_inicio]
                            
                            total_por_acao = float(divs_filtrados.sum())
                            ativo.total_dividendos = total_por_acao * ativo.quantidade_atual
                        else:
                            ativo.total_dividendos = 0
                except Exception as e:
                    print(f"Erro calculando dividendos {ativo.ticker}: {e}")
                
                ativo.save()

                # --- CÁLCULO 3: VALUATION (Graham & Bazin) ---
                try:
                    # Para Valuation, precisamos do .info completo
                    info = stock.info
                    score = 0
                    recomendacao = "NEUTRO"
                    detalhes = {}

                    if ativo.tipo == 'ACAO' or ativo.tipo == 'FII':
                        dy = (info.get('dividendYield', 0) or 0) * 100
                        pvp = info.get('priceToBook', 0) or 0
                        pl = info.get('trailingPE', 0) or 0
                        
                        # Critérios Visuais
                        if dy > 6 and 0 < pvp < 1.5: score = 5; recomendacao = "COMPRAR"
                        elif dy > 4: score = 3; recomendacao = "MANTER"
                        else: score = 1; recomendacao = "REVISAR"
                        
                        detalhes = {'dy': dy, 'pvp': pvp, 'pl': pl}
                    
                    elif ativo.tipo == 'CRIPTO':
                        score = 3; recomendacao = "MANTER"; detalhes = {}

                    AnaliseBot.objects.update_or_create(
                        ativo=ativo,
                        defaults={
                            'preco_atual': preco_atual,
                            'recomendacao': recomendacao,
                            'pontuacao': score,
                            'pl': detalhes.get('pl', 0),
                            'pvp': detalhes.get('pvp', 0),
                            'dy': detalhes.get('dy', 0)
                        }
                    )
                except Exception as e:
                    print(f"Erro Valuation {ativo.ticker}: {e}")

        except Exception as e:
            print(f"Erro Crítico {ativo.ticker}: {e}")

# --- 3. FUNÇÃO DE RADAR (Mantida, pois usa requests puro) ---
def buscar_oportunidades_mercado():
    print("--- [DEBUG] 1. Iniciando busca no Fundamentus ---")
    url = 'https://www.fundamentus.com.br/resultado.php'
    
    try:
        # AQUI PRECISAMOS DA SESSÃO/HEADERS, pois não é yfinance
        r = requests.get(url, headers=get_headers())
        r.raise_for_status()
        
        df = pd.read_html(StringIO(r.text), decimal=',', thousands='.', attrs={'id': 'resultado'})[0]
        
        # Limpeza
        for col in ['Div.Yield', 'Mrg Ebit', 'Mrg. Líq.', 'ROIC', 'ROE', 'Cresc. Rec.5a']:
            df[col] = df[col].astype(str).str.replace('.', '').str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce') / 100

        for col in ['Liq.2meses', 'Patrim. Líq']:
            df[col] = df[col].astype(str).str.replace('.', '').str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Filtros
        df = df[df['Liq.2meses'] > 1000000]
        df = df[(df['P/L'] > 0.01) & (df['P/L'] <= 15)]
        df = df[(df['P/VP'] > 0.01) & (df['P/VP'] <= 1.5)]
        df = df[df['Div.Yield'] > 0.06]
        df = df[df['ROE'] > 0.10]

        df = df.sort_values(by='Div.Yield', ascending=False)
        top_20 = df.head(20)
        
        resultados = []
        for index, row in top_20.iterrows():
            resultados.append({
                'ticker': row['Papel'],
                'tipo': 'ACAO', 
                'preco': float(row['Cotação']) / 100 if float(row['Cotação']) > 1000 else float(row['Cotação']),
                'score': 5,
                'recomendacao': "COMPRA FORTE",
                'detalhes': {
                    'dy': row['Div.Yield'] * 100,
                    'pl': row['P/L'],
                    'pvp': row['P/VP'],
                    'roe': row['ROE'] * 100
                }
            })
        
        return resultados

    except Exception as e:
        print(f"--- [DEBUG] ERRO CRÍTICO NO SCREENER: {e} ---")
        return []