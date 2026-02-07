import time
import threading
import pandas as pd
import ta
import yfinance as yf
from tkinter import *
from tkinter import ttk
from datetime import datetime

# ================= VARIÁVEIS GLOBAIS =================
rodando = False
PAR = "EURUSD=X"
TIMEFRAME = "1m"
EXPIRACAO = 1
ESTRATEGIA = "RSI + EMA"

TIMEFRAMES_YF = ["1m","2m","5m","15m","30m","60m","90m","1d","5d","1wk","1mo"]
EXPIRACOES = list(range(1,31))

# ================= UTILIDADES =================
def calcular_forca_vela(df):
    u = df.iloc[-1]
    corpo = abs(u['close'] - u['open'])
    range_total = u['high'] - u['low']
    if range_total < 0.00001:
        range_total = corpo if corpo > 0 else 0.00001
    return round((corpo / range_total) * 100, 1)

def calcular_forca_sinal(sinal_tipo, forca_vela, rsi=50, macd_diff=0, stochastic_diff=0, bb_diff=0):
    base = forca_vela * 0.5
    rsi_factor = max(0, 50 - abs(50 - rsi)) * 0.3
    macd_factor = abs(macd_diff) * 10
    stochastic_factor = abs(stochastic_diff) * 5
    bb_factor = abs(bb_diff) * 5
    if sinal_tipo in ["📈 CALL", "📉 PUT"]:
        return min(round(base + rsi_factor + macd_factor + stochastic_factor + bb_factor, 1), 100)
    return 0

# ================= ESTRATÉGIAS =================
def estrategia_rsi_ema(df):
    u = df.iloc[-1]; a = df.iloc[-2]
    forca_vela = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['rsi'] < 45 and a['ema9'] < a['ema21'] and u['ema9'] > u['ema21']: sinal, cor = "📈 CALL", "#00ff99"
    elif u['rsi'] > 55 and a['ema9'] > a['ema21'] and u['ema9'] < u['ema21']: sinal, cor = "📉 PUT", "#ff5555"
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'])
    return sinal, cor, forca_vela, forca_sinal

def estrategia_ema_trend(df):
    u = df.iloc[-1]; forca_vela = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['ema9'] > u['ema21'] and u['rsi'] > 45: sinal, cor = "📈 CALL", "#00ffaa"
    elif u['ema9'] < u['ema21'] and u['rsi'] < 55: sinal, cor = "📉 PUT", "#ff6666"
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'])
    return sinal, cor, forca_vela, forca_sinal

def estrategia_rsi_extremo(df):
    u = df.iloc[-1]; forca_vela = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['rsi'] <= 30: sinal, cor = "📈 CALL", "#00ff99"
    elif u['rsi'] >= 70: sinal, cor = "📉 PUT", "#ff5555"
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'])
    return sinal, cor, forca_vela, forca_sinal

def estrategia_macd(df):
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd(); df['signal'] = macd.macd_signal()
    a, u = df.iloc[-2], df.iloc[-1]; forca_vela = calcular_forca_vela(df)
    macd_diff = u['macd'] - u['signal']
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['macd'] < a['signal'] and u['macd'] > u['signal']: sinal, cor = "📈 CALL", "#00ff99"
    elif a['macd'] > a['signal'] and u['macd'] < u['signal']: sinal, cor = "📉 PUT", "#ff5555"
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'], macd_diff=macd_diff)
    return sinal, cor, forca_vela, forca_sinal

def estrategia_confluencia(df):
    u = df.iloc[-1]; forca_vela = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['ema9'] > u['ema21'] and 40 < u['rsi'] < 55: sinal, cor = "📈 CALL", "#00ffaa"
    elif u['ema9'] < u['ema21'] and 45 < u['rsi'] < 60: sinal, cor = "📉 PUT", "#ff6666"
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'])
    return sinal, cor, forca_vela, forca_sinal

def estrategia_bollinger(df):
    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_high'] = bb.bollinger_hband(); df['bb_low'] = bb.bollinger_lband()
    u = df.iloc[-1]; forca_vela = calcular_forca_vela(df)
    sinal, cor, bb_diff = "⏳ AGUARDAR", "yellow", 0
    if u['close'] < u['bb_low']: sinal, cor, bb_diff = "📈 CALL", "#00ff99", u['bb_low'] - u['close']
    elif u['close'] > u['bb_high']: sinal, cor, bb_diff = "📉 PUT", "#ff5555", u['close'] - u['bb_high']
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'], bb_diff=bb_diff)
    return sinal, cor, forca_vela, forca_sinal

def estrategia_stochastic(df):
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch'] = stoch.stoch(); df['stoch_signal'] = stoch.stoch_signal()
    u, a = df.iloc[-1], df.iloc[-2]; forca_vela = calcular_forca_vela(df)
    sinal, cor, stochastic_diff = "⏳ AGUARDAR", "yellow", 0
    if a['stoch'] < a['stoch_signal'] and u['stoch'] > u['stoch_signal']: sinal, cor, stochastic_diff = "📈 CALL", "#00ff99", u['stoch']-u['stoch_signal']
    elif a['stoch'] > a['stoch_signal'] and u['stoch'] < u['stoch_signal']: sinal, cor, stochastic_diff = "📉 PUT", "#ff5555", u['stoch_signal']-u['stoch']
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'], stochastic_diff=stochastic_diff)
    return sinal, cor, forca_vela, forca_sinal

def estrategia_suporte_resistencia(df):
    u = df.iloc[-1]; forca_vela = calcular_forca_vela(df)
    N, tolerancia = 20, 0.002
    suporte = df['low'][-N:].min(); resistencia = df['high'][-N:].max()
    sinal, cor, sr_diff = "⏳ AGUARDAR", "yellow", 0
    if abs(u['close'] - suporte)/suporte <= tolerancia: sinal, cor, sr_diff = "📈 CALL", "#00ff99", suporte-u['close']
    elif abs(u['close'] - resistencia)/resistencia <= tolerancia: sinal, cor, sr_diff = "📉 PUT", "#ff5555", u['close']-resistencia
    forca_sinal = calcular_forca_sinal(sinal, forca_vela, u['rsi'], bb_diff=sr_diff)
    return sinal, cor, forca_vela, forca_sinal

ESTRATEGIAS = {
    "RSI + EMA": estrategia_rsi_ema,
    "EMA Trend": estrategia_ema_trend,
    "RSI Extremo": estrategia_rsi_extremo,
    "MACD": estrategia_macd,
    "Confluência PRO": estrategia_confluencia,
    "Bollinger Bands": estrategia_bollinger,
    "Stochastic": estrategia_stochastic,
    "Suporte/Resistência": estrategia_suporte_resistencia
}

# ================= FUNÇÕES DE CONTROLE =================
def aplicar_config():
    global PAR, TIMEFRAME, EXPIRACAO, ESTRATEGIA
    PAR = par_var.get(); TIMEFRAME = tf_var.get(); EXPIRACAO = int(exp_var.get()); ESTRATEGIA = est_var.get()
    status_label.config(text=f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m | {ESTRATEGIA}", fg="cyan")

def parar():
    global rodando
    rodando = False
    sinal_label.config(text="⏹️ Parado", fg="white")

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        threading.Thread(target=analisar, daemon=True).start()
        sinal_label.config(text="▶ Rodando...", fg="white")

# ================= FUNÇÃO DE ANÁLISE =================
def analisar():
    global rodando
    while rodando:
        try:
            data = yf.download(PAR, period="5d", interval=TIMEFRAME, progress=False)
            if data.empty: time.sleep(10); continue
            df = pd.DataFrame()
            df['open'], df['high'], df['low'], df['close'] = data['Open'], data['High'], data['Low'], data['Close']
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
            df['ema9'] = ta.trend.EMAIndicator(df['close'], 9).ema_indicator()
            df['ema21'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()
            df.dropna(inplace=True)
            if len(df) < 20: time.sleep(10); continue
            sinal, cor, forca_vela, forca_sinal = ESTRATEGIAS[ESTRATEGIA](df)
            agora = datetime.now().strftime("%H:%M:%S")
            tempo_restante = 60 - datetime.now().second
            root.after(0, atualizar_sinal, sinal, cor, forca_vela, forca_sinal, tempo_restante)
            if sinal != "⏳ AGUARDAR":
                registro = f"{agora} | {ESTRATEGIA} | {sinal} | Força Sinal: {forca_sinal}%"
                root.after(0, lambda reg=registro: adicionar_historico(reg))
        except Exception as e:
            print("Erro:", e)
        time.sleep(15)

# ================= FUNÇÕES DE UI =================
def atualizar_sinal(sinal, cor, forca_vela, forca_sinal, tempo_restante):
    sinal_label.config(text=sinal, fg=cor)
    forca_vela_label.config(text=f"Força Vela: {forca_vela}%", fg="green" if forca_vela>=60 else "yellow" if forca_vela>=30 else "red")
    forca_sinal_label.config(text=f"Força Sinal: {forca_sinal}%", fg="green" if forca_sinal>=60 else "yellow" if forca_sinal>=30 else "red")
    tempo_label.config(text=f"⏱ {tempo_restante}s")
    par_label.config(text=f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m")

def adicionar_historico(texto):
    historico_box.insert(END, texto)
    historico_box.yview_moveto(1)
    if historico_box.size() > 50: historico_box.delete(0)

# ================= INTERFACE =================
root = Tk()
root.title("Rafiki Trader PRO")
root.geometry("650x850")
root.configure(bg="#0d0d0d")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# === ABA TRADER ===
frame_trader = Frame(notebook, bg="#0d0d0d")
notebook.add(frame_trader, text="Trader")

Label(frame_trader, text="RAFIKI TRADER PRO", fg="cyan", bg="#0d0d0d", font=("Arial",16,"bold")).pack(pady=10)
status_label = Label(frame_trader, text=f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m | {ESTRATEGIA}", fg="white", bg="#0d0d0d")
status_label.pack(pady=5)

# Configurações
Label(frame_trader,text="Par (Yahoo Finance)", fg="white", bg="#0d0d0d").pack()
par_var = StringVar(value=PAR)
Entry(frame_trader,textvariable=par_var,width=25).pack()
Label(frame_trader,text="Timeframe", fg="white", bg="#0d0d0d").pack(pady=5)
tf_var = StringVar(value=TIMEFRAME)
ttk.Combobox(frame_trader,textvariable=tf_var,values=TIMEFRAMES_YF,state="readonly", width=22).pack()
Label(frame_trader,text="Expiração (min)", fg="white", bg="#0d0d0d").pack(pady=5)
exp_var = StringVar(value=str(EXPIRACAO))
ttk.Combobox(frame_trader,textvariable=exp_var,values=EXPIRACOES,state="readonly", width=22).pack()
Label(frame_trader,text="Estratégia", fg="white", bg="#0d0d0d").pack(pady=5)
est_var = StringVar(value=ESTRATEGIA)
ttk.Combobox(frame_trader,textvariable=est_var,values=list(ESTRATEGIAS.keys()),state="readonly", width=25).pack()
Button(frame_trader,text="🔄 Aplicar Configurações", command=aplicar_config,bg="#444",fg="white", width=30).pack(pady=15)

# Sinal
frame_sinal = Frame(frame_trader,bg="#0d0d0d")
frame_sinal.pack(pady=15,fill="x")
sinal_label = Label(frame_sinal,text="---", fg="white", bg="#0d0d0d", font=("Arial",18,"bold"))
sinal_label.pack(pady=5)
frame_detalhes = Frame(frame_sinal,bg="#0d0d0d")
frame_detalhes.pack(pady=5)

forca_vela_label = Label(frame_detalhes,text="Força Vela: 0%", fg="white", bg="#0d0d0d", font=("Arial",12))
forca_vela_label.grid(row=0,column=0,padx=10)
forca_sinal_label = Label(frame_detalhes,text="Força Sinal: 0%", fg="white", bg="#0d0d0d", font=("Arial",12))
forca_sinal_label.grid(row=0,column=1,padx=10)
tempo_label = Label(frame_detalhes,text="⏱ 0s", fg="white", bg="#0d0d0d", font=("Arial",12))
tempo_label.grid(row=0,column=2,padx=10)
par_label = Label(frame_detalhes,text=f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m", fg="cyan", bg="#0d0d0d", font=("Arial",12))
par_label.grid(row=0,column=3,padx=10)

# Histórico
Label(frame_trader,text="Histórico de Sinais", fg="white", bg="#0d0d0d").pack()
historico_box = Listbox(frame_trader,width=80,height=8,bg="#111",fg="white")
historico_box.pack(pady=10)

# Botões
Button(frame_trader,text="▶ INICIAR", command=iniciar, bg="#00aa88", fg="black", width=25).pack(pady=5)
Button(frame_trader,text="■ PARAR", command=parar, bg="#aa3333", fg="white", width=25).pack()

# === ABA MAPA DE ESTRATÉGIAS ESTÁTICO ===
frame_mapa = Frame(notebook, bg="#0d0d0d")
notebook.add(frame_mapa, text="Mapa de Estratégias")

Label(frame_mapa, text="Mapa de Estratégias - Rafiki Trader PRO", fg="cyan", bg="#0d0d0d", font=("Arial",14,"bold")).pack(pady=10)

tabela_frame = Frame(frame_mapa, bg="#0d0d0d")
tabela_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

# Cabeçalho
cabecalho = ["Estratégia", "Como Usar"]
for col, text in enumerate(cabecalho):
    Label(
        tabela_frame, 
        text=text, 
        fg="white", 
        bg="#222", 
        font=("Arial",12,"bold"), 
        width=35, 
        borderwidth=1, 
        relief="solid"
    ).grid(row=0, column=col, sticky="nsew")


# Linhas da tabela completas
linhas = [
    ["RSI + EMA", """Timeframe: 1m-5m | Expiração: 1-3m
Entrada: CALL se RSI <45 e cruzamento de EMA9 sobre EMA21
PUT se RSI >55 e EMA9 cruzando abaixo EMA21"""],
    ["EMA Trend", """Timeframe: 5m-15m | Expiração: 3-5m
Entrada: Seguir tendência EMA9 vs EMA21
RSI >45 CALL | RSI <55 PUT"""],
    ["RSI Extremo", """Timeframe: 1m-5m | Expiração: 1-2m
Entrada: RSI <=30 CALL | RSI >=70 PUT"""],
    ["MACD", """Timeframe: 5m | Expiração: 3-5m
Entrada: Cruzamento MACD acima da linha de sinal CALL
Cruzamento abaixo PUT"""],
    ["Confluência PRO", """Timeframe: 1m-5m | Expiração: 1-3m
Entrada: EMA9 > EMA21 + RSI 40-55 CALL
EMA9 < EMA21 + RSI 45-60 PUT"""],
    ["Bollinger Bands", """Timeframe: 1m-5m | Expiração: 1-2m
Entrada: Preço toca banda inferior CALL
Preço toca banda superior PUT"""],
    ["Stochastic", """Timeframe: 1m-5m | Expiração: 1-2m
Entrada: Cruzamento Stochastic acima linha de sinal CALL
Cruzamento abaixo PUT"""],
    ["Suporte/Resistência", """Timeframe: 5m | Expiração: 3-5m
Entrada: Próximo ao suporte CALL
Próximo à resistência PUT
Tolerância: 0.2%"""]
]


# Inserindo linhas na tabela
for row_index, linha in enumerate(linhas, start=1):
    for col_index, valor in enumerate(linha):
        Label(
            tabela_frame,
            text=valor,
            fg="white",
            bg="#111",
            font=("Arial",11),
            width=35,
            borderwidth=1,
            relief="solid",
            wraplength=300,
            justify="left"
        ).grid(row=row_index, column=col_index, sticky="nsew")

# Configura colunas para expandirem
for i in range(len(cabecalho)):
    tabela_frame.grid_columnconfigure(i, weight=1)


# ================= INICIA A APLICAÇÃO =================
root.mainloop()
