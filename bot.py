import time
import threading
import pandas as pd
import ta
import yfinance as yf
from tkinter import *
from tkinter import ttk

rodando = False

# CONFIG PADRÃO
PAR = "EURUSD=X"
TIMEFRAME = "1m"
EXPIRACAO = 1
ESTRATEGIA = "RSI + EMA"

# ================= ESTRATÉGIAS =================
def estrategia_rsi_ema(df):
    u = df.iloc[-1]

    if u['rsi'] < 35 and u['ema9'] > u['ema21']:
        return "📈 CALL", "#00ff99"

    if u['rsi'] > 65 and u['ema9'] < u['ema21']:
        return "📉 PUT", "#ff5555"

    return "⏳ AGUARDAR", "yellow"


def estrategia_rsi_puro(df):
    u = df.iloc[-1]

    if u['rsi'] < 35:
        return "📈 CALL", "#00ff99"

    if u['rsi'] > 65:
        return "📉 PUT", "#ff5555"

    return "⏳ AGUARDAR", "yellow"


def estrategia_ema(df):
    u = df.iloc[-1]

    if u['ema9'] > u['ema21']:
        return "📈 CALL", "#00ff99"

    if u['ema9'] < u['ema21']:
        return "📉 PUT", "#ff5555"

    return "⏳ AGUARDAR", "yellow"


ESTRATEGIAS = {
    "RSI + EMA": estrategia_rsi_ema,
    "RSI Extremos": estrategia_rsi_puro,
    "EMA Tendência": estrategia_ema
}

# ================= CORE =================
def analisar():
    global rodando
    while rodando:
        try:
            data = yf.download(
                tickers=PAR,
                period="2d",
                interval=TIMEFRAME,
                progress=False
            )

            if data.empty:
                sinal_label.config(text="⏳ Sem dados", fg="orange")
                time.sleep(30)
                continue

            df = pd.DataFrame()
            df['close'] = data['Close']
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
            df['ema9'] = ta.trend.EMAIndicator(df['close'], 9).ema_indicator()
            df['ema21'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()
            df.dropna(inplace=True)

            if len(df) < 5:
                sinal_label.config(text="⏳ Calculando...", fg="orange")
                time.sleep(30)
                continue

            sinal, cor = ESTRATEGIAS[ESTRATEGIA](df)

            info = f"{sinal}\nTF: {TIMEFRAME.upper()} | EXP: {EXPIRACAO}m"
            sinal_label.config(text=info, fg=cor)

        except Exception as e:
            sinal_label.config(text="⚠ ERRO", fg="red")
            print("Erro:", e)

        time.sleep(EXPIRACAO * 60)

# ================= CONTROLES =================
def iniciar():
    global rodando
    if not rodando:
        rodando = True
        threading.Thread(target=analisar, daemon=True).start()


def parar():
    global rodando
    rodando = False
    sinal_label.config(text="⏹️ Parado", fg="white")


def aplicar_config():
    global PAR, TIMEFRAME, EXPIRACAO, ESTRATEGIA
    PAR = par_var.get()
    TIMEFRAME = tf_var.get()
    EXPIRACAO = int(exp_var.get())
    ESTRATEGIA = est_var.get()

    status_label.config(
        text=f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m | {ESTRATEGIA}",
        fg="cyan"
    )

# ================= INTERFACE =================
root = Tk()
root.title("Bot de sinais - Trader")
root.geometry("460x560")
root.configure(bg="#0d0d0d")

Label(root, text="BOT DO RAFIKI",
      fg="cyan", bg="#0d0d0d",
      font=("Arial", 15, "bold")).pack(pady=10)

status_label = Label(root,
    text="EURUSD | M1 | EXP 1m | RSI + EMA",
    fg="white", bg="#0d0d0d")
status_label.pack(pady=5)

# PAR
Label(root, text="Par (Yahoo Finance)", fg="white", bg="#0d0d0d").pack()
par_var = StringVar(value="EURUSD=X")
Entry(root, textvariable=par_var, width=25).pack()

# TIMEFRAME
Label(root, text="Timeframe", fg="white", bg="#0d0d0d").pack(pady=5)
tf_var = StringVar(value="1m")
ttk.Combobox(root, textvariable=tf_var,
    values=["1m", "5m", "15m"],
    state="readonly", width=22).pack()

# EXPIRAÇÃO
Label(root, text="Expiração (min)", fg="white", bg="#0d0d0d").pack(pady=5)
exp_var = StringVar(value="1")
ttk.Combobox(root, textvariable=exp_var,
    values=["1", "2", "3", "5"],
    state="readonly", width=22).pack()

# ESTRATÉGIA
Label(root, text="Estratégia", fg="white", bg="#0d0d0d").pack(pady=5)
est_var = StringVar(value="RSI + EMA")
ttk.Combobox(root, textvariable=est_var,
    values=list(ESTRATEGIAS.keys()),
    state="readonly", width=25).pack()

Button(root, text="🔄 Aplicar Configurações",
       command=aplicar_config,
       bg="#444", fg="white",
       width=30).pack(pady=15)

sinal_label = Label(root, text="---",
    fg="white", bg="#0d0d0d",
    font=("Arial", 22, "bold"))
sinal_label.pack(pady=25)

Button(root, text="▶ Iniciar",
    command=iniciar,
    bg="#00aa88", fg="black",
    width=22).pack(pady=5)

Button(root, text="■ Parar",
    command=parar,
    bg="#aa3333", fg="white",
    width=22).pack()

root.mainloop()
