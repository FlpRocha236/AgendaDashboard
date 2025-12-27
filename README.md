# 💰 My OS — Sistema Financeiro Inteligente

Um sistema completo para **gestão financeira pessoal**, análise de investimentos e apoio à tomada de decisões estratégicas.

O **My OS** funciona como um verdadeiro **sistema operacional financeiro**, centralizando dados, automatizando análises e gerando insights inteligentes para melhorar a saúde financeira do usuário.

---

## 🎯 Objetivo do Projeto

Criar uma plataforma capaz de:

- Organizar a vida financeira pessoal  
- Analisar investimentos com critérios profissionais  
- Automatizar decisões financeiras  
- Gerar relatórios claros, objetivos e acionáveis  

O sistema vai além de uma planilha tradicional, atuando como um **consultor financeiro digital**.

---

## ✨ Funcionalidades Principais

### 📊 1. Controle Financeiro
- Cadastro de receitas e despesas  
- Classificação por categorias  
- Gestão de cartões de crédito (limite, fatura e vencimento)  
- Controle de contas a pagar com alertas visuais  

---

### 🤖 2. Graham AI – Robô de Investimentos
Sistema inteligente baseado nos métodos de **Benjamin Graham** e **Décio Bazin**.

Funcionalidades:
- Cálculo automático de indicadores:
  - P/L (Preço/Lucro)
  - P/VP (Preço/Valor Patrimonial)
  - Dividend Yield
  - ROE
- Filtros inteligentes de valuation  
- Recomendações automáticas:
  - ✅ Compra  
  - ⚠️ Manter  
  - ❌ Venda  
- Suporte a:
  - Ações (B3)
  - Fundos Imobiliários (FIIs)
  - Criptomoedas  

---

### 🏥 3. Módulo de Saúde Financeira
Avaliação completa da situação financeira do usuário, incluindo:

- **Score financeiro (0 a 100)**  
- Análise da taxa de poupança  
- Avaliação do nível de endividamento  
- Diagnóstico automático com sugestões de melhoria  

---

### 📡 4. Radar de Mercado
- Monitoramento contínuo de ativos financeiros  
- Sistema de **Graceful Degradation**, garantindo funcionamento mesmo quando APIs externas falham  
- Uso de dados simulados para manter estabilidade do sistema  

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologias |
|------|-------------|
| Backend | Python 3.10, Django 5 |
| Banco de Dados | SQLite (Dev) / MySQL (Prod) |
| Análise de Dados | Pandas, NumPy, yFinance |
| Frontend | HTML5, CSS3, Bootstrap 5 |
| Testes | Unittest |
| Deploy | PythonAnywhere |

---

## 🚀 Como Executar o Projeto

```bash
# Clonar o repositório
git clone https://github.com/FlpRocha236/AgendaDashboard.git

# Acessar a pasta
cd AgendaDashboard

# Criar ambiente virtual
python -m venv venv

# Ativar o ambiente
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Iniciar o servidor
python manage.py runserver
```

---

## 🧪 Testes Automatizados

O projeto conta com testes unitários para garantir a confiabilidade das regras de negócio.
```bash
python manage.py test core
```

## 📄 Licença

Este projeto está licenciado sob a MIT License — uso livre para fins pessoais e comerciais.

## 👨‍💻 Autor

Felipe Rocha
Desenvolvedor de Software | Sistemas Financeiros | Automação & Dados