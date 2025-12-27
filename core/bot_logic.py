import yfinance as yf
from .models import Ativo, AnaliseBot

def executar_analise_carteira(user):
    ativos = Ativo.objects.filter(user=user)
    
    # 1. Calcula o Patrimônio Total para Rebalanceamento (Cripto/ETF)
    total_patrimonio = sum(a.total_investido() for a in ativos)
    
    for ativo in ativos:
        # Prepara o Ticker para o Yahoo Finance
        if ativo.tipo == 'CRIPTO':
            # Ex: BTC -> BTC-USD (ou BTC-BRL se preferir)
            ticker_yf = f"{ativo.ticker}-BRL"
        elif ativo.ticker.endswith('.SA'):
            ticker_yf = ativo.ticker
        else:
            ticker_yf = f"{ativo.ticker}.SA"

        try:
            stock = yf.Ticker(ticker_yf)
            info = stock.info
            
            # --- DADOS GERAIS ---
            preco = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
            
            # Inicializa variáveis
            score = 0
            recomendacao = "NEUTRO"
            msg_analise = ""
            
            # ==========================================================
            # ESTRATÉGIA 1: AÇÕES (Graham & Bazin - Valor e Dividendos)
            # ==========================================================
            if ativo.tipo == 'ACAO':
                pl = info.get('trailingPE', 0) or 0
                pvp = info.get('priceToBook', 0) or 0
                dy = (info.get('dividendYield', 0) or 0) * 100
                roe = (info.get('returnOnEquity', 0) or 0) * 100
                divida_pl = info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0
                
                # Checklist
                c_dy = dy >= 6.0              # Paga mais que a Renda Fixa?
                c_pl = 0 < pl <= 15.0         # Está barata?
                c_pvp = 0 < pvp <= 1.5        # Preço justo patrimonial?
                c_roe = roe >= 10.0           # Empresa eficiente?
                c_divida = divida_pl <= 1.5   # Dívida saudável?
                
                score = sum([c_dy, c_pl, c_pvp, c_roe, c_divida])
                
                if score >= 4:
                    recomendacao = "APORTAR (Oportunidade)"
                elif score == 3:
                    recomendacao = "MANTER (Fundamentos Ok)"
                else:
                    recomendacao = "REVISAR (Caro ou Ruim)"

                # Salva dados específicos de Ação
                atualizar_banco(ativo, preco, recomendacao, score, pl=pl, pvp=pvp, dy=dy, roe=roe, divida=divida_pl)

            # ==========================================================
            # ESTRATÉGIA 2: FIIs (Foco em Renda Passiva e P/VP)
            # ==========================================================
            elif ativo.tipo == 'FII': # Vamos assumir que você cadastrou como 'ACAO' ou criar um tipo novo depois
                # FIIs no Yahoo as vezes vem com dados faltando, focamos no DY
                dy = (info.get('dividendYield', 0) or 0) * 100
                pvp = info.get('priceToBook', 0) or 0
                
                # Checklist FII
                # DY Anual > 8% (aprox 0.65% ao mês)
                c_dy = dy >= 8.0 
                # P/VP entre 0.80 (desconto) e 1.10 (aceitável)
                c_pvp = 0.8 <= pvp <= 1.10
                
                if c_dy and c_pvp:
                    score = 5
                    recomendacao = "COMPRAR (Bom Yield e Preço)"
                elif c_dy:
                    score = 3
                    recomendacao = "MANTER (Pagando bem)"
                else:
                    score = 1
                    recomendacao = "AGUARDAR"
                
                atualizar_banco(ativo, preco, recomendacao, score, pvp=pvp, dy=dy)

            # ==========================================================
            # ESTRATÉGIA 3: CRIPTO (Rebalanceamento de Carteira)
            # ==========================================================
            elif ativo.tipo == 'CRIPTO':
                # Meta: Ter 5% da carteira em Cripto
                META_PERCENTUAL = 5.0
                
                # Quanto eu tenho hoje disso?
                valor_investido_neste = ativo.total_investido()
                if total_patrimonio > 0:
                    percentual_atual = (valor_investido_neste / total_patrimonio) * 100
                else:
                    percentual_atual = 0

                # Lógica de Rebalanceamento
                if percentual_atual < (META_PERCENTUAL - 1): # Ex: Tenho 3%, meta é 5%
                    score = 5
                    recomendacao = "COMPRAR (Abaixo da meta)"
                elif percentual_atual > (META_PERCENTUAL + 2): # Ex: Tenho 8%, Bitcoin subiu muito
                    score = 1
                    recomendacao = "VENDER PARTE (Acima da meta)"
                else:
                    score = 3
                    recomendacao = "MANTER (Dentro da meta)"

                # Para cripto, P/L e Dividendos não existem, mandamos 0
                atualizar_banco(ativo, preco, recomendacao, score)

        except Exception as e:
            print(f"Erro ao analisar {ativo.ticker}: {e}")

def atualizar_banco(ativo, preco, recomendacao, score, pl=0, pvp=0, dy=0, roe=0, divida=0):
    AnaliseBot.objects.update_or_create(
        ativo=ativo,
        defaults={
            'preco_atual': preco,
            'recomendacao': recomendacao,
            'pontuacao': score,
            'pl': pl,
            'pvp': pvp,
            'dy': dy,
            'roe': roe,
            'divida_liquida_pl': divida,
            # Atualiza os booleanos para o visual (lógica simplificada para visualização)
            'criterio_dy': dy >= 6,
            'criterio_pl': 0 < pl <= 15,
            'criterio_pvp': 0 < pvp <= 1.5,
            'criterio_roe': roe >= 10,
            'criterio_divida': divida <= 1.5
        }
    )