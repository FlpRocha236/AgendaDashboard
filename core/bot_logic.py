import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from .models import Ativo, AnaliseBot

# --- 1. CONFIGURAÇÃO DE DISFARCE (User-Agent) ---
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

# --- 2. FUNÇÃO DE ANÁLISE DA CARTEIRA (Mantida igual, usando Yahoo) ---
def executar_analise_carteira(user):
    ativos = Ativo.objects.filter(user=user)
    total_patrimonio = sum(a.total_investido() for a in ativos)
    
    session = requests.Session()
    session.headers.update(get_headers())

    for ativo in ativos:
        # Prepara ticker para o Yahoo
        if ativo.tipo == 'CRIPTO': ticker_yf = f"{ativo.ticker}-BRL"
        elif ativo.ticker.endswith('.SA'): ticker_yf = ativo.ticker
        else: ticker_yf = f"{ativo.ticker}.SA"

        try:
            stock = yf.Ticker(ticker_yf, session=session)
            
            # Tenta pegar info de forma segura
            try:
                info = stock.info
            except:
                continue 

            # Normalização de dados para carteira pessoal (Yahoo)
            preco = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            score = 0
            recomendacao = "NEUTRO"
            
            # Lógica Simplificada para Carteira
            if ativo.tipo == 'ACAO' or ativo.tipo == 'FII':
                dy = (info.get('dividendYield', 0) or 0) * 100
                pvp = info.get('priceToBook', 0) or 0
                pl = info.get('trailingPE', 0) or 0
                
                # Critério básico visual
                if dy > 6 and 0 < pvp < 1.5: score = 5; recomendacao = "COMPRAR"
                elif dy > 4: score = 3; recomendacao = "MANTER"
                else: score = 1; recomendacao = "REVISAR"
                
                detalhes = {'dy': dy, 'pvp': pvp, 'pl': pl}
            
            elif ativo.tipo == 'CRIPTO':
                percentual = (ativo.total_investido() / total_patrimonio * 100) if total_patrimonio > 0 else 0
                if percentual < 4: score, recomendacao = 5, "COMPRAR"
                elif percentual > 7: score, recomendacao = 1, "VENDER"
                else: score, recomendacao = 3, "MANTER"
                detalhes = {}

            # Salvar no banco
            AnaliseBot.objects.update_or_create(
                ativo=ativo,
                defaults={
                    'preco_atual': preco,
                    'recomendacao': recomendacao,
                    'pontuacao': score,
                    'pl': detalhes.get('pl', 0),
                    'pvp': detalhes.get('pvp', 0),
                    'dy': detalhes.get('dy', 0)
                }
            )
        except Exception as e:
            print(f"Erro Carteira {ativo.ticker}: {e}")

# --- 3. NOVA FUNÇÃO: SCREENER DE MERCADO (FUNDAMENTUS) ---
def buscar_oportunidades_mercado():
    """
    Acessa o site Fundamentus, baixa TODAS as ações e filtra as melhores.
    """
    url = 'https://www.fundamentus.com.br/resultado.php'
    
    try:
        # 1. Baixar a tabela bruta do site
        r = requests.get(url, headers=get_headers())
        r.raise_for_status()
        
        # 2. Ler com Pandas (lxml necessário)
        df = pd.read_html(StringIO(r.text), decimal=',', thousands='.')[0]
        
        # 3. Limpeza de Dados (Transformar texto em número)
        # Remove % e pontos, troca vírgula por ponto
        for col in ['Div.Yield', 'Mrg Ebit', 'Mrg. Líq.', 'ROIC', 'ROE', 'Cresc. Rec.5a']:
            df[col] = df[col].astype(str).str.replace('.', '').str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce') / 100

        # Liq.2meses e Patr.Liq vem como string com pontos
        for col in ['Liq.2meses', 'Patrim. Líq']:
            df[col] = df[col].astype(str).str.replace('.', '').str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 4. APLICAÇÃO DOS FILTROS (A Mágica de Graham/Bazin)
        # Filtro 1: Liquidez diária > R$ 1 Milhão (pra não pegar micos)
        df = df[df['Liq.2meses'] > 1000000]
        
        # Filtro 2: P/L positivo e barato (entre 0.01 e 15)
        df = df[(df['P/L'] > 0.01) & (df['P/L'] <= 15)]
        
        # Filtro 3: P/VP justo (entre 0.01 e 1.5)
        df = df[(df['P/VP'] > 0.01) & (df['P/VP'] <= 1.5)]
        
        # Filtro 4: Dividend Yield > 6% (Estratégia Bazin)
        df = df[df['Div.Yield'] > 0.06]
        
        # Filtro 5: ROE > 10% (Empresas eficientes)
        df = df[df['ROE'] > 0.10]

        # 5. RANKING FINAL
        # Ordenar pelo maior Dividend Yield
        df = df.sort_values(by='Div.Yield', ascending=False)
        
        # Pega as TOP 20
        top_20 = df.head(20)
        
        # 6. Formata para enviar ao Template HTML
        resultados = []
        for index, row in top_20.iterrows():
            resultados.append({
                'ticker': row['Papel'],
                'tipo': 'ACAO', # Fundamentus mistura Ações e FIIs, mas a maioria aqui será Ação
                'preco': float(row['Cotação']) / 100 if float(row['Cotação']) > 1000 else float(row['Cotação']), # Ajuste fino se necessário
                'score': 5, # Se passou no filtro acima, é nota 5
                'detalhes': {
                    'dy': row['Div.Yield'] * 100,
                    'pl': row['P/L'],
                    'pvp': row['P/VP'],
                    'roe': row['ROE'] * 100
                }
            })
            
        return resultados

    except Exception as e:
        print(f"Erro no Screener Fundamentus: {e}")
        return []