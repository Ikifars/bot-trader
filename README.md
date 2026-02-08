💹 Rafiki Trader Engine PRO
Rafiki Trader Engine é um software de análise técnica em tempo real para o mercado financeiro (Forex/Opções Binárias), desenvolvido em Python. Ele utiliza bibliotecas de alta precisão para monitorar ativos via Yahoo Finance e identificar oportunidades baseadas em confluências de indicadores.

🚀 Funcionalidades Principais
Multiestratégias: 10 estratégias integradas, incluindo Sniper PRO, CCI Reversa, RSI Extremo e Suporte/Resistência H1.

Painel Técnico Ajustável: Calibragem em tempo real de períodos de RSI, EMAs, Bandas de Bollinger, MACD e Stochastic.

Filtro de Volatilidade: Sistema inteligente que alerta sobre horários de notícias e alta volatilidade.

Análise de Confluência: Cálculo automático de "Força da Vela" e "Nível de Confiança" para cada sinal emitido.

Alertas Sonoros: Notificação por áudio sempre que uma oportunidade de entrada é detectada.

Histórico de Sinais: Log detalhado das operações sugeridas durante a sessão.

🛠️ Tecnologias Utilizadas
Python 3.x

Pandas & TA (Technical Analysis Library): Para processamento de dados e indicadores.

YFinance: Para streaming de dados do mercado.

Tkinter: Interface gráfica (GUI) intuitiva e leve.

Threading: Processamento em segundo plano para não travar a interface.

📋 Como Instalar
Clone o repositório:

Bash
git clone https://github.com/seu-usuario/rafiki-trader-engine.git
Instale as dependências necessárias:

Bash
pip install pandas ta yfinance
Nota: A biblioteca tkinter e winsound já costumam vir instaladas nativamente no Python para Windows.

🚦 Como Usar
Execute o arquivo principal: python main.py.

No campo Par, digite o ativo desejado (Ex: EURUSD=X, BTC-USD).

Escolha o Timeframe (1m, 5m, 15m, etc).

Selecione sua Estratégia de preferência.

Clique em 🔄 APLICAR TUDO para calibrar os indicadores.

Clique em ▶ INICIAR MOTOR para começar o monitoramento.
