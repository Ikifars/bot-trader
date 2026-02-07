import time
import threading
import pandas as pd
import ta
import yfinance as yf
from tkinter import *
from tkinter import ttk
from datetime import datetime
import winsound

# ================= CONFIGURAÇÕES TÉCNICAS ADAPTÁVEIS =================
CONFIG = {
    "RSI_PERIODO": 14,
    "EMA_CURTA": 9,
    "EMA_LONGA": 21,
    "EMA_TENDENCIA": 100,
    "ADX_PERIODO": 14,
    "ADX_MINIMO": 25,
    "CCI_PERIODO": 20,
    "CCI_EXTREMO": 100,
}

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

def calcular_forca_sinal(sinal_tipo, forca_vela, rsi=50, macd_diff=0, stochastic_diff=0, bb_diff=0, adx=0):
    if "AGUARDAR" in sinal_tipo: return 0
    base = forca_vela * 0.4
    rsi_factor = max(0, 50 - abs(50 - rsi)) * 0.2
    adx_factor = (adx / 100) * 15
    return min(round(base + rsi_factor + adx_factor + 30, 1), 100)

# ================= ESTRATÉGIAS =================
def estrategia_sniper_pro(df):
    u = df.iloc[-1]
    tendencia_alta = u['close'] > u['ema_trend']
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['close'] <= u['bb_low'] and u['rsi'] < 30 and tendencia_alta and u['adx'] > CONFIG["ADX_MINIMO"]:
        sinal, cor = "📈 CALL SNIPER", "#00ff99"
    elif u['close'] >= u['bb_high'] and u['rsi'] > 70 and not tendencia_alta and u['adx'] > CONFIG["ADX_MINIMO"]:
        sinal, cor = "📉 PUT SNIPER", "#ff5555"
    fv = calcular_forca_vela(df)
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_cci_reversa(df):
    u = df.iloc[-1]
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['cci'] < -CONFIG["CCI_EXTREMO"]: sinal, cor = "📈 CALL CCI", "#00ffff"
    elif u['cci'] > CONFIG["CCI_EXTREMO"]: sinal, cor = "📉 PUT CCI", "#ff00ff"
    fv = calcular_forca_vela(df)
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'])

def estrategia_rsi_ema(df):
    u = df.iloc[-1]; a = df.iloc[-2]
    fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['rsi'] < 45 and a['ema9'] < a['ema21'] and u['ema9'] > u['ema21']: sinal, cor = "📈 CALL", "#00ff99"
    elif u['rsi'] > 55 and a['ema9'] > a['ema21'] and u['ema9'] < u['ema21']: sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_ema_trend(df):
    u = df.iloc[-1]; fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['ema9'] > u['ema21'] and u['rsi'] > 45: sinal, cor = "📈 CALL", "#00ffaa"
    elif u['ema9'] < u['ema21'] and u['rsi'] < 55: sinal, cor = "📉 PUT", "#ff6666"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_rsi_extremo(df):
    u = df.iloc[-1]; fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['rsi'] <= 30: sinal, cor = "📈 CALL", "#00ff99"
    elif u['rsi'] >= 70: sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_macd(df):
    macd = ta.trend.MACD(df['close'])
    df['macd_val'] = macd.macd(); df['macd_signal'] = macd.macd_signal()
    a, u = df.iloc[-2], df.iloc[-1]; fv = calcular_forca_vela(df)
    macd_diff = u['macd_val'] - u['macd_signal']
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['macd_val'] < a['macd_signal'] and u['macd_val'] > u['macd_signal']: sinal, cor = "📈 CALL", "#00ff99"
    elif a['macd_val'] > a['macd_signal'] and u['macd_val'] < u['macd_signal']: sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], macd_diff=macd_diff, adx=u['adx'])

def estrategia_confluencia(df):
    u = df.iloc[-1]; fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['ema9'] > u['ema21'] and 40 < u['rsi'] < 55: sinal, cor = "📈 CALL", "#00ffaa"
    elif u['ema9'] < u['ema21'] and 45 < u['rsi'] < 60: sinal, cor = "📉 PUT", "#ff6666"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_bollinger(df):
    u = df.iloc[-1]; fv = calcular_forca_vela(df)
    sinal, cor, bb_diff = "⏳ AGUARDAR", "yellow", 0
    if u['close'] < u['bb_low']: sinal, cor, bb_diff = "📈 CALL", "#00ff99", u['bb_low'] - u['close']
    elif u['close'] > u['bb_high']: sinal, cor, bb_diff = "📉 PUT", "#ff5555", u['close'] - u['bb_high']
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], bb_diff=bb_diff, adx=u['adx'])

def estrategia_stochastic(df):
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch(); df['stoch_d'] = stoch.stoch_signal()
    u, a = df.iloc[-1], df.iloc[-2]; fv = calcular_forca_vela(df)
    sinal, cor, stoch_diff = "⏳ AGUARDAR", "yellow", 0
    if a['stoch_k'] < a['stoch_d'] and u['stoch_k'] > u['stoch_d']: sinal, cor, stoch_diff = "📈 CALL", "#00ff99", u['stoch_k']-u['stoch_d']
    elif a['stoch_k'] > a['stoch_d'] and u['stoch_k'] < u['stoch_d']: sinal, cor, stoch_diff = "📉 PUT", "#ff5555", u['stoch_d']-u['stoch_k']
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], stochastic_diff=stoch_diff, adx=u['adx'])

def estrategia_suporte_resistencia(df):
    u = df.iloc[-1]; fv = calcular_forca_vela(df)
    N, tolerancia = 20, 0.002
    suporte = df['low'][-N:].min(); resistencia = df['high'][-N:].max()
    sinal, cor, sr_diff = "⏳ AGUARDAR", "yellow", 0
    if abs(u['close'] - suporte)/suporte <= tolerancia: sinal, cor, sr_diff = "📈 CALL", "#00ff99", suporte-u['close']
    elif abs(u['close'] - resistencia)/resistencia <= tolerancia: sinal, cor, sr_diff = "📉 PUT", "#ff5555", u['close']-resistencia
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], bb_diff=sr_diff, adx=u['adx'])

ESTRATEGIAS = {
    "Sniper Precisão": estrategia_sniper_pro,
    "CCI Reversa": estrategia_cci_reversa,
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
    global PAR, TIMEFRAME, EXPIRACAO, ESTRATEGIA, CONFIG
    try:
        PAR = par_var.get()
        TIMEFRAME = tf_var.get()
        EXPIRACAO = int(exp_var.get())
        ESTRATEGIA = est_var.get()
        
        # Atualiza o dicionário técnico com os valores da interface
        CONFIG["RSI_PERIODO"] = int(rsi_p_var.get())
        CONFIG["EMA_CURTA"] = int(ema_c_var.get())
        CONFIG["EMA_LONGA"] = int(ema_l_var.get())
        CONFIG["EMA_TENDENCIA"] = int(ema_t_var.get())
        CONFIG["ADX_PERIODO"] = int(adx_p_var.get())
        CONFIG["ADX_MINIMO"] = int(adx_m_var.get())
        CONFIG["CCI_PERIODO"] = int(cci_p_var.get())
        CONFIG["CCI_EXTREMO"] = int(cci_e_var.get())
        
        status_label.config(text=f"CONFIGURADO: {PAR} | {TIMEFRAME.upper()} | {ESTRATEGIA}", fg="cyan")
    except Exception as e:
        status_label.config(text="Erro: Use apenas números inteiros nos indicadores", fg="red")

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

# ================= MOTOR DE ANÁLISE =================
def analisar():
    global rodando
    ultimo_minuto_analisado = -1
    while rodando:
        try:
            agora = datetime.now()
            if agora.second >= 57 or agora.second <= 2:
                if agora.minute != ultimo_minuto_analisado:
                    data = yf.download(PAR, period="2d", interval=TIMEFRAME, progress=False)
                    if not data.empty:
                        df = data[['Open', 'High', 'Low', 'Close']].copy()
                        df.columns = ['open', 'high', 'low', 'close']
                        
                        # Cálculos usando as variáveis do CONFIG (que são alteradas na UI)
                        df['rsi'] = ta.momentum.RSIIndicator(df['close'], CONFIG["RSI_PERIODO"]).rsi()
                        df['ema9'] = ta.trend.EMAIndicator(df['close'], CONFIG["EMA_CURTA"]).ema_indicator()
                        df['ema21'] = ta.trend.EMAIndicator(df['close'], CONFIG["EMA_LONGA"]).ema_indicator()
                        df['ema_trend'] = ta.trend.EMAIndicator(df['close'], CONFIG["EMA_TENDENCIA"]).ema_indicator()
                        df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], CONFIG["ADX_PERIODO"]).adx()
                        df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close'], CONFIG["CCI_PERIODO"]).cci()
                        
                        bb = ta.volatility.BollingerBands(df['close'])
                        df['bb_high'], df['bb_low'] = bb.bollinger_hband(), bb.bollinger_lband()
                        
                        df.dropna(inplace=True)
                        sinal, cor, f_v, f_s = ESTRATEGIAS[ESTRATEGIA](df)

                        root.after(0, atualizar_sinal, sinal, cor, f_v, f_s)
                        if "AGUARDAR" not in sinal:
                            winsound.Beep(1000, 500)
                            registro = f"{agora.strftime('%H:%M:%S')} | {sinal} | Força: {f_s}%"
                            root.after(0, lambda reg=registro: adicionar_historico(reg))
                    ultimo_minuto_analisado = agora.minute
            
            tempo_reg = 60 - agora.second
            root.after(0, lambda t=tempo_reg: tempo_label.config(text=f"⏱ Próxima Vela: {t}s"))
            time.sleep(1)
        except Exception as e:
            print("Erro:", e); time.sleep(5)

# ================= FUNÇÕES DE UI =================
def atualizar_sinal(sinal, cor, f_v, f_s):
    sinal_label.config(text=sinal, fg=cor)
    forca_vela_label.config(text=f"Força Vela: {f_v}%", fg="green" if f_v>=60 else "yellow")
    forca_sinal_label.config(text=f"Força Sinal: {f_s}%", fg="green" if f_s>=60 else "yellow")
    par_label.config(text=f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m")

def adicionar_historico(texto):
    historico_box.insert(0, texto)
    if historico_box.size() > 50: historico_box.delete(50)

# ================= INTERFACE =================
root = Tk()
root.title("Rafiki Trader PRO")
root.geometry("650x950")
root.configure(bg="#0d0d0d")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

frame_trader = Frame(notebook, bg="#0d0d0d")
notebook.add(frame_trader, text="Trader")

Label(frame_trader, text="RAFIKI TRADER PRO", fg="cyan", bg="#0d0d0d", font=("Arial",16,"bold")).pack(pady=10)
status_label = Label(frame_trader, text="Configure e clique em Aplicar", fg="white", bg="#0d0d0d")
status_label.pack()

# --- ABA DE CONFIGURAÇÕES DE ATIVO ---
f_ativo = LabelFrame(frame_trader, text=" Ativo e Estratégia ", fg="yellow", bg="#0d0d0d", padx=10, pady=10)
f_ativo.pack(pady=5, fill="x", padx=20)

par_var = StringVar(value=PAR); Entry(f_ativo, textvariable=par_var, width=15).grid(row=0, column=1)
Label(f_ativo, text="Par:", fg="white", bg="#0d0d0d").grid(row=0, column=0)

tf_var = StringVar(value=TIMEFRAME); ttk.Combobox(f_ativo, textvariable=tf_var, values=TIMEFRAMES_YF, width=10).grid(row=0, column=3)
Label(f_ativo, text=" TF:", fg="white", bg="#0d0d0d").grid(row=0, column=2)

est_var = StringVar(value=ESTRATEGIA); ttk.Combobox(f_ativo, textvariable=est_var, values=list(ESTRATEGIAS.keys()), width=20).grid(row=1, column=1, pady=5)
Label(f_ativo, text="Estratégia:", fg="white", bg="#0d0d0d").grid(row=1, column=0)

exp_var = StringVar(value="1"); ttk.Combobox(f_ativo, textvariable=exp_var, values=EXPIRACOES, width=5).grid(row=1, column=3)
Label(f_ativo, text=" Exp:", fg="white", bg="#0d0d0d").grid(row=1, column=2)

# --- ABA DE CONFIGURAÇÕES DE INDICADORES (NOVO) ---
f_tecnico = LabelFrame(frame_trader, text=" Ajustes Técnicos dos Indicadores ", fg="cyan", bg="#0d0d0d", padx=10, pady=10)
f_tecnico.pack(pady=5, fill="x", padx=20)

# Linha 1: RSI e Médias
rsi_p_var = StringVar(value="14"); Entry(f_tecnico, textvariable=rsi_p_var, width=5).grid(row=0, column=1)
Label(f_tecnico, text="RSI Período:", fg="white", bg="#0d0d0d").grid(row=0, column=0, sticky="w")

ema_c_var = StringVar(value="9"); Entry(f_tecnico, textvariable=ema_c_var, width=5).grid(row=0, column=3)
Label(f_tecnico, text=" EMA Curta:", fg="white", bg="#0d0d0d").grid(row=0, column=2, sticky="w")

ema_l_var = StringVar(value="21"); Entry(f_tecnico, textvariable=ema_l_var, width=5).grid(row=0, column=5)
Label(f_tecnico, text=" EMA Longa:", fg="white", bg="#0d0d0d").grid(row=0, column=4, sticky="w")

# Linha 2: ADX e CCI
adx_p_var = StringVar(value="14"); Entry(f_tecnico, textvariable=adx_p_var, width=5).grid(row=1, column=1, pady=5)
Label(f_tecnico, text="ADX Período:", fg="white", bg="#0d0d0d").grid(row=1, column=0, sticky="w")

adx_m_var = StringVar(value="25"); Entry(f_tecnico, textvariable=adx_m_var, width=5).grid(row=1, column=3)
Label(f_tecnico, text=" ADX Mínimo:", fg="white", bg="#0d0d0d").grid(row=1, column=2, sticky="w")

ema_t_var = StringVar(value="100"); Entry(f_tecnico, textvariable=ema_t_var, width=5).grid(row=1, column=5)
Label(f_tecnico, text=" EMA Trend:", fg="white", bg="#0d0d0d").grid(row=1, column=4, sticky="w")

# Linha 3: CCI
cci_p_var = StringVar(value="20"); Entry(f_tecnico, textvariable=cci_p_var, width=5).grid(row=2, column=1)
Label(f_tecnico, text="CCI Período:", fg="white", bg="#0d0d0d").grid(row=2, column=0, sticky="w")

cci_e_var = StringVar(value="100"); Entry(f_tecnico, textvariable=cci_e_var, width=5).grid(row=2, column=3)
Label(f_tecnico, text=" CCI Extremo:", fg="white", bg="#0d0d0d").grid(row=2, column=2, sticky="w")

Button(frame_trader, text="🔄 APLICAR TUDO", command=aplicar_config, bg="#444", fg="white", font=("Arial", 10, "bold")).pack(pady=10, fill="x", padx=40)

# --- SINAIS E HISTÓRICO ---
sinal_label = Label(frame_trader, text="---", fg="white", bg="#0d0d0d", font=("Arial", 22, "bold")); sinal_label.pack()
f_info = Frame(frame_trader, bg="#0d0d0d")
f_info.pack(pady=5)
forca_vela_label = Label(f_info, text="Força Vela: 0%", fg="white", bg="#0d0d0d"); forca_vela_label.grid(row=0, column=0, padx=10)
forca_sinal_label = Label(f_info, text="Força Sinal: 0%", fg="white", bg="#0d0d0d"); forca_sinal_label.grid(row=0, column=1, padx=10)
tempo_label = Label(frame_trader, text="⏱ 0s", fg="yellow", bg="#0d0d0d", font=("Arial", 12)); tempo_label.pack()
par_label = Label(frame_trader, text="---", fg="cyan", bg="#0d0d0d"); par_label.pack()

historico_box = Listbox(frame_trader, width=70, height=6, bg="#111", fg="white"); historico_box.pack(pady=10)

btn_f = Frame(frame_trader, bg="#0d0d0d")
btn_f.pack()
Button(btn_f, text="▶ INICIAR", command=iniciar, bg="#00aa88", width=20).grid(row=0, column=0, padx=5)
Button(btn_f, text="■ PARAR", command=parar, bg="#aa3333", width=20, fg="white").grid(row=0, column=1, padx=5)

# === ABA MAPA DE ESTRATÉGIAS (Sua Aba Original) ===
frame_mapa = Frame(notebook, bg="#0d0d0d")
notebook.add(frame_mapa, text="Mapa de Estratégias")
tabela_frame = Frame(frame_mapa, bg="#0d0d0d")
tabela_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

linhas = [
    ["Sniper Precisão (NOVA)", "Bollinger + RSI + EMA100 + ADX. Reversão técnica com filtro de força."],
    ["CCI Reversa (NOVA)", "Baseada em exaustão de preço via Commodity Channel Index."],
    ["RSI + EMA", "Entrada: CALL se RSI <45 e cruzamento EMA9 > EMA21 | PUT se RSI >55 e EMA9 < EMA21"],
    ["EMA Trend", "Seguir tendência EMA9 vs EMA21 | RSI >45 CALL | RSI <55 PUT"],
    ["RSI Extremo", "Entrada: RSI <=30 CALL | RSI >=70 PUT"],
    ["MACD", "Cruzamento MACD acima do sinal CALL | Cruzamento abaixo PUT"],
    ["Confluência PRO", "EMA9 > EMA21 + RSI 40-55 CALL | EMA9 < EMA21 + RSI 45-60 PUT"],
    ["Bollinger Bands", "Preço toca banda inferior CALL | Preço toca banda superior PUT"],
    ["Stochastic", "Cruzamento Stochastic acima do sinal CALL | Cruzamento abaixo PUT"],
    ["Suporte/Resistência", "Próximo ao suporte CALL | Próximo à resistência PUT"]
]
for r, linha in enumerate(linhas):
    for c, valor in enumerate(linha):
        Label(tabela_frame, text=valor, fg="white", bg="#111", borderwidth=1, relief="solid", wraplength=300).grid(row=r, column=c, sticky="nsew")

root.mainloop()
