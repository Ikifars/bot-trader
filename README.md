# 📈 Trading Signal Bot (Binary Options Analyzer)

Bot analisador de mercado desenvolvido em **Python**, com **interface gráfica**, focado em gerar **sinais de CALL / PUT** para operações em **opções binárias** (ex.: IQ Option, Pocket Option).

> ⚠️ Importante:  
> Este projeto **NÃO executa operações automaticamente**.  
> Ele funciona como **ferramenta de apoio à decisão**, analisando dados de mercado e exibindo sinais com base em regras objetivas.

---

## 🎯 Objetivo do Projeto

Criar uma aplicação capaz de:
- Analisar candles de mercado em tempo real
- Aplicar estratégias técnicas objetivas
- Exibir sinais claros (CALL / PUT / AGUARDAR)
- Evitar dependência de APIs proprietárias de corretoras
- Oferecer uma interface simples, funcional e extensível

O foco é **educacional, técnico e demonstrativo**, ideal para portfólio de desenvolvimento.

---

## 🧠 Estratégia (Padrão)

A estratégia padrão utiliza:

- **RSI (14)** – identificação de sobrecompra/sobrevenda  
- **EMA 9 e EMA 21** – cruzamento de médias  
- **Timeframe:** 1 minuto (M1)

### Regras básicas
- 📈 **CALL**
  - RSI < 30
  - EMA 9 cruza acima da EMA 21
- 📉 **PUT**
  - RSI > 70
  - EMA 9 cruza abaixo da EMA 21
- ⏳ **AGUARDAR**
  - Quando não há confluência suficiente

> O código foi estruturado para permitir **troca fácil de estratégia**.

---

## 🖥️ Interface Gráfica

Interface desenvolvida com **Tkinter**, exibindo:
- Par analisado
- Timeframe
- Sinal atual (CALL / PUT / AGUARDAR)
- Controles de iniciar e parar análise

Design simples e funcional, priorizando clareza e estabilidade.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **Tkinter** – interface gráfica
- **pandas** – manipulação de dados
- **ta** – indicadores técnicos
- **yfinance** – obtenção de dados de mercado

---

## 📦 Instalação

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/Ikifars/bot-trader
cd seu-repositorio
python -m pip install pandas ta yfinance
python bot.py

````

## PAR = "EURUSD=X"
## PAR = "GBPUSD=X"
## PAR = "USDJPY=X"


🔧 Alterar ou Criar Estratégias

As estratégias estão isoladas dentro da função de análise, permitindo:
criação de múltiplas estratégias
alternância rápida
testes e melhorias contínuas
O projeto foi pensado para extensão e refatoração futura.

⚠️ Aviso Legal

Este projeto:
Não garante lucros
Não executa ordens automaticamente
Não se conecta diretamente a contas de corretoras
Não deve ser utilizado como único critério de decisão financeira
Uso educacional e experimental.

👨‍💻 Autor
Raphael Victor (Rafiki)
Desenvolvedor em formação, focado em:

Python
Análise de dados
Automação
Interfaces gráficas
Soluções práticas para mercado real

📫 Contato: raphaelvictor016@gmail.com

