import time
import threading
import pandas as pd
import ta
import yfinance as yf
from tkinter import *
from tkinter import ttk
from datetime import datetime

rodando = False

# CONFIG PADRÃO
PAR = "EURUSD=X"
TIMEFRAME = "1m"
EXPIRACAO = 1
ESTRATEGIA = "RSI + EMA"

# ================= ESTRATÉGIAS =================

def estrategia_rsi_ema(df):
    a = df.iloc[-2]
    u = df.iloc[-1]

    forca = "FRACO"
    if u['rsi'] < 40 or u['rsi'] > 60:
        forca = "MÉDIO"
    if u['rsi'] < 35 or u['rsi'] > 65:
        forca = "FORTE"

    if u['rsi'] < 45 and a['ema9'] < a['ema21'] and u['ema9'] > u['ema21']:
        return "📈 CALL", "#00ff99", forca

    if u['rsi'] > 55 and a['ema9'] > a['ema21'] and u['ema9'] < u['ema21']:
        return "📉 PUT", "#ff5555", forca

    return "⏳ AGUARDAR", "yellow", "—"


def estrategia_ema_trend(df):
    u = df.iloc[-1]

    if u['ema9'] > u['ema21'] and u['rsi'] > 45:
        return "📈 CALL", "#00ffaa", "TENDÊNCIA"

    if u['ema9'] < u['ema21'] and u['rsi'] < 55:
        return "📉 PUT", "#ff6666", "TENDÊNCIA"

    return "⏳ AGUARDAR", "yellow", "—"


def estrategia_rsi_extremo(df):
    u = df.iloc[-1]

    if u['rsi'] <= 30:
        return "📈 CALL", "#00ff99", "EXTREMO"

    if u['rsi'] >= 70:
        return "📉 PUT", "#ff5555", "EXTREMO"

    return "⏳ AGUARDAR", "yellow", "—"


def estrategia_macd(df):
    a = df.iloc[-2]
    u = df.iloc[-1]

    if a['macd'] < a['signal'] and u['macd'] > u['signal']:
        return "📈 CALL", "#00ff99", "MACD"

    if a['macd'] > a['signal'] and u['macd'] < u['signal']:
        return "📉 PUT", "#ff5555", "MACD"

    return "⏳ AGUARDAR", "yellow", "—"


def estrategia_confluencia(df):
    u = df.iloc[-1]

    if u['ema9'] > u['ema21'] and 40 < u['rsi'] < 55:
        return "📈 CALL", "#00ffaa", "ALTA"

    if u['ema9'] < u['ema21'] and 45 < u['rsi'] < 60:
        return "📉 PUT", "#ff6666", "ALTA"

    return "⏳ AGUARDAR", "yellow", "—"


ESTRATEGIAS = {
    "RSI + EMA": estrategia_rsi_ema,
    "EMA Trend": estrategia_ema_trend,
    "RSI Extremo": estrategia_rsi_extremo,
    "MACD": estrategia_macd,
    "Confluência PRO": estrategia_confluencia
}

# ================= UI SAFE =================

def atualizar_sinal(texto, cor):
    sinal_label.config(text=texto, fg=cor)

def adicionar_historico(texto):
    if historico_box.size() >= 50:
        historico_box.delete(0)
    historico_box.insert(END, texto)
    historico_box.yview_moveto(1)

# ================= CORE =================

def analisar():
    global rodando

    while rodando:
        try:
            data = yf.download(
                tickers=PAR,
                period="5d",
                interval=TIMEFRAME,
                progress=False
            )

            if data.empty:
                time.sleep(10)
                continue

            df = pd.DataFrame()
            df['close'] = data['Close']
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
            df['ema9'] = ta.trend.EMAIndicator(df['close'], 9).ema_indicator()
            df['ema21'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()

            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['signal'] = macd.macd_signal()

            df.dropna(inplace=True)

            if len(df) < 20:
                time.sleep(10)
                continue

            sinal, cor, forca = ESTRATEGIAS[ESTRATEGIA](df)

            agora = datetime.now().strftime("%H:%M:%S")
            tempo_restante = 60 - datetime.now().second

            texto = (
                f"{sinal}\n"
                f"Força: {forca}\n"
                f"⏱ Vela: {tempo_restante}s\n"
                f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m"
            )

            root.after(0, atualizar_sinal, texto, cor)

            if sinal != "⏳ AGUARDAR":
                registro = f"{agora} | {ESTRATEGIA} | {sinal} | {forca}"
                root.after(0, adicionar_historico, registro)

        except Exception as e:
            print("Erro:", e)

        time.sleep(20)

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
root.title("Rafiki Trader PRO")
root.geometry("520x720")
root.configure(bg="#0d0d0d")

Label(root, text="RAFIKI TRADER PRO",
      fg="cyan", bg="#0d0d0d",
      font=("Arial", 16, "bold")).pack(pady=10)

status_label = Label(
    root,
    text="EURUSD | M1 | EXP 1m | RSI + EMA",
    fg="white", bg="#0d0d0d"
)
status_label.pack(pady=5)

Label(root, text="Par (Yahoo Finance)", fg="white", bg="#0d0d0d").pack()
par_var = StringVar(value=PAR)
Entry(root, textvariable=par_var, width=25).pack()

Label(root, text="Timeframe", fg="white", bg="#0d0d0d").pack(pady=5)
tf_var = StringVar(value=TIMEFRAME)
ttk.Combobox(root, textvariable=tf_var,
             values=["1m", "5m", "15m"],
             state="readonly", width=22).pack()

Label(root, text="Expiração (min)", fg="white", bg="#0d0d0d").pack(pady=5)
exp_var = StringVar(value=str(EXPIRACAO))
ttk.Combobox(root, textvariable=exp_var,
             values=["1", "2", "3", "5"],
             state="readonly", width=22).pack()

Label(root, text="Estratégia", fg="white", bg="#0d0d0d").pack(pady=5)
est_var = StringVar(value=ESTRATEGIA)
ttk.Combobox(root, textvariable=est_var,
             values=list(ESTRATEGIAS.keys()),
             state="readonly", width=25).pack()

Button(root, text="🔄 Aplicar Configurações",
       command=aplicar_config,
       bg="#444", fg="white",
       width=30).pack(pady=15)

sinal_label = Label(root, text="---",
                    fg="white", bg="#0d0d0d",
                    font=("Arial", 20, "bold"))
sinal_label.pack(pady=15)

Label(root, text="Histórico de Sinais",
      fg="white", bg="#0d0d0d").pack()
historico_box = Listbox(root, width=55, height=8,
                        bg="#111", fg="white")
historico_box.pack(pady=10)

Button(root, text="▶ INICIAR",
       command=iniciar,
       bg="#00aa88", fg="black",
       width=25).pack(pady=5)

Button(root, text="■ PARAR",
       command=parar,
       bg="#aa3333", fg="white",
       width=25).pack()

root.mainloop()
