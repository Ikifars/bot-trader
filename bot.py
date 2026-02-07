import time
import threading
import pandas as pd
import ta
import yfinance as yf
from tkinter import *

rodando = False
PAR = "EURUSD=X"

def analisar():
    global rodando
    while rodando:
        try:
            data = yf.download(
                tickers=PAR,
                period="1d",
                interval="1m",
                progress=False
            )

            if data.empty:
                sinal_label.config(text="⏳ Sem dados", fg="orange")
                time.sleep(60)
                continue

            close = data['Close']

            df = pd.DataFrame()
            df['close'] = close
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
            df['ema9'] = ta.trend.EMAIndicator(df['close'], 9).ema_indicator()
            df['ema21'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()

            # REMOVE LINHAS COM NaN
            df.dropna(inplace=True)

            if len(df) < 5:
                sinal_label.config(text="⏳ Calculando...", fg="orange")
                time.sleep(60)
                continue

            ultima = df.iloc[-1]
            anterior = df.iloc[-2]

            if ultima['rsi'] < 30 and anterior['ema9'] < anterior['ema21'] and ultima['ema9'] > ultima['ema21']:
                sinal_label.config(text="📈 CALL", fg="#00ff99")

            elif ultima['rsi'] > 70 and anterior['ema9'] > anterior['ema21'] and ultima['ema9'] < ultima['ema21']:
                sinal_label.config(text="📉 PUT", fg="#ff5555")

            else:
                sinal_label.config(text="⏳ AGUARDAR", fg="yellow")

        except Exception as e:
            sinal_label.config(text="⚠ Erro lógico", fg="red")
            print("Erro real:", e)

        time.sleep(60)


def iniciar():
    global rodando
    rodando = True
    threading.Thread(target=analisar, daemon=True).start()

def parar():
    global rodando
    rodando = False
    sinal_label.config(text="⏹️ Parado", fg="white")

# ===== INTERFACE =====
root = Tk()
root.title("Pocket Option Signal Bot")
root.geometry("380x260")
root.configure(bg="#0d0d0d")

Label(root, text="POCKET OPTION SIGNAL BOT",
      fg="cyan", bg="#0d0d0d",
      font=("Arial", 14, "bold")).pack(pady=10)

Label(root, text="Par: EURUSD | TF: M1",
      fg="white", bg="#0d0d0d").pack()

sinal_label = Label(root, text="---",
                    fg="white", bg="#0d0d0d",
                    font=("Arial", 22, "bold"))
sinal_label.pack(pady=30)

Button(root, text="▶ Iniciar",
       command=iniciar,
       bg="#00aa88", fg="black",
       width=15).pack(pady=5)

Button(root, text="■ Parar",
       command=parar,
       bg="#aa3333", fg="white",
       width=15).pack()

root.mainloop()
