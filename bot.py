import time
import threading
import pandas as pd
import ta
import yfinance as yf
from tkinter import *
from tkinter import ttk
from datetime import datetime
import winsound
import random

# ================= CONFIGURAÇÕES TÉCNICAS PADRÃO =================
CONFIG = {
    "RSI_PERIODO": 14,
    "RSI_UPPER": 70,
    "RSI_LOWER": 30,
    "EMA_CURTA": 9,
    "EMA_LONGA": 21,
    "EMA_TENDENCIA": 100,
    "ADX_PERIODO": 14,
    "ADX_MINIMO": 25,
    "CCI_PERIODO": 20,
    "CCI_EXTREMO": 100,
    "BB_PERIODO": 20,
    "BB_DESVIO": 2,
    "STOCH_K": 14,
    "STOCH_D": 3,
    "MACD_FAST": 12,
    "MACD_SLOW": 26
}

rodando = False
PAR = "EURUSD=X"
TIMEFRAME = "1m"
EXPIRACAO = 1
ESTRATEGIA = "RSI + EMA"
PLACAR = {"WIN": 0, "LOSS": 0} # Novo: Controle de Placar

TIMEFRAMES_YF = ["1m","2m","5m","15m","30m","60m","90m","1d","5d","1wk","1mo"]
EXPIRACOES = list(range(1,31))

# ================= NOVO: SISTEMA DE ALERTA DE NOTÍCIAS =================
def verificar_status_mercado():
    agora = datetime.now()
    if agora.minute in [0, 1, 2, 29, 30, 31, 59]:
        return "⚠️ ALTA VOLATILIDADE (Notícias Próximas)", "#ffaa00"
    return "✅ MERCADO ESTÁVEL (Técnico Respeitando)", "#00ff00"

# ================= NOVO: DETECÇÃO DE PREÇO H1 E TENDÊNCIA =================
def detectar_niveis_h1(par):
    try:
        data_h1 = yf.download(par, period="5d", interval="60m", progress=False)
        if data_h1.empty: return [], []
        data_h1.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in data_h1.columns]
        resistencias = data_h1['high'].nlargest(5).tolist()
        suportes = data_h1['low'].nsmallest(5).tolist()
        return suportes, resistencias
    except: return [], []

def verificar_tendencia_macro(par):
    try:
        data_h1 = yf.download(par, period="5d", interval="60m", progress=False)
        data_h1.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in data_h1.columns]
        ema_macro = ta.trend.EMAIndicator(data_h1['close'], window=100).ema_indicator()
        if data_h1['close'].iloc[-1] > ema_macro.iloc[-1]: return "ALTA"
        return "BAIXA"
    except: return "INDEFINIDA"

# ================= UTILIDADES DE CONFLUÊNCIA =================
def calcular_forca_vela(df):
    try:
        u = df.iloc[-1]
        corpo = abs(u['close'] - u['open'])
        range_total = u['high'] - u['low']
        if range_total < 0.000001: return 50.0
        return round((corpo / range_total) * 100, 1)
    except: return 50.0

def medir_confluencia_total(df, sinal_tipo):
    if "AGUARDAR" in sinal_tipo: return 0
    u = df.iloc[-1]
    pontos = 0
    if u['rsi'] > CONFIG["RSI_UPPER"] or u['rsi'] < CONFIG["RSI_LOWER"]: pontos += 25
    if u['adx'] > CONFIG["ADX_MINIMO"]: pontos += 25
    if u['close'] > u['bb_high'] or u['close'] < u['bb_low']: pontos += 30
    if (u['close'] > u['ema_trend'] and "CALL" in sinal_tipo) or (u['close'] < u['ema_trend'] and "PUT" in sinal_tipo):
        pontos += 20
    return min(pontos, 100)

# ================= ESTRATÉGIAS =================
def estrategia_sniper_pro(df):
    u = df.iloc[-1]; a = df.iloc[-2]
    sinal, cor = "⏳ AGUARDAR", "yellow"
    call = (u['close'] <= u['bb_low'] and u['rsi'] < CONFIG["RSI_LOWER"] and u['adx'] > CONFIG["ADX_MINIMO"] and u['close'] > u['ema_trend'])
    put = (u['close'] >= u['bb_high'] and u['rsi'] > CONFIG["RSI_UPPER"] and u['adx'] > CONFIG["ADX_MINIMO"] and u['close'] < u['ema_trend'])
    if call: sinal, cor = "📈 CALL SNIPER", "#00ff99"
    elif put: sinal, cor = "📉 PUT SNIPER", "#ff5555"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_cci_reversa(df):
    u = df.iloc[-1]; a = df.iloc[-2]
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['cci'] < -CONFIG["CCI_EXTREMO"] and u['cci'] > a['cci']:
        sinal, cor = "📈 CALL CCI", "#00ffff"
    elif a['cci'] > CONFIG["CCI_EXTREMO"] and u['cci'] < a['cci']:
        sinal, cor = "📉 PUT CCI", "#ff00ff"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_rsi_ema(df):
    u = df.iloc[-1]; a = df.iloc[-2]
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['ema9'] < a['ema21'] and u['ema9'] > u['ema21'] and u['rsi'] < 50:
        sinal, cor = "📈 CALL", "#00ff99"
    elif a['ema9'] > a['ema21'] and u['ema9'] < u['ema21'] and u['rsi'] > 50:
        sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_ema_trend(df):
    u = df.iloc[-1]; sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['close'] > u['ema_trend'] and u['ema9'] > u['ema21'] and u['rsi'] > 50:
        sinal, cor = "📈 CALL TREND", "#00ffaa"
    elif u['close'] < u['ema_trend'] and u['ema9'] < u['ema21'] and u['rsi'] < 50:
        sinal, cor = "📉 PUT TREND", "#ff6666"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_rsi_extremo(df):
    u = df.iloc[-1]; a = df.iloc[-2]; sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['rsi'] <= CONFIG["RSI_LOWER"]: sinal, cor = "📈 CALL", "#00ff99"
    elif u['rsi'] >= CONFIG["RSI_UPPER"]: sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_macd(df):
    a, u = df.iloc[-2], df.iloc[-1]; sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['macd_val'] < a['macd_signal'] and u['macd_val'] > u['macd_signal']:
        sinal, cor = "📈 CALL MACD", "#00ff99"
    elif a['macd_val'] > a['macd_signal'] and u['macd_val'] < u['macd_signal']:
        sinal, cor = "📉 PUT MACD", "#ff5555"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_confluencia(df):
    u = df.iloc[-1]; sinal, cor = "⏳ AGUARDAR", "yellow"
    cond_call = (u['rsi'] < 40 and u['ema9'] > u['ema21'] and u['close'] < u['bb_low'])
    cond_put = (u['rsi'] > 60 and u['ema9'] < u['ema21'] and u['close'] > u['bb_high'])
    if cond_call: sinal, cor = "📈 CALL CONF", "#00ffaa"
    elif cond_put: sinal, cor = "📉 PUT CONF", "#ff6666"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_bollinger(df):
    u = df.iloc[-1]; sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['close'] <= u['bb_low']: sinal, cor = "📈 CALL BB", "#00ff99"
    elif u['close'] >= u['bb_high']: sinal, cor = "📉 PUT BB", "#ff5555"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_stochastic(df):
    u, a = df.iloc[-1], df.iloc[-2]; sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['stoch_k'] < a['stoch_d'] and u['stoch_k'] > u['stoch_d'] and u['stoch_k'] < 20:
        sinal, cor = "📈 CALL STOCH", "#00ff99"
    elif a['stoch_k'] > a['stoch_d'] and u['stoch_k'] < u['stoch_d'] and u['stoch_k'] > 80:
        sinal, cor = "📉 PUT STOCH", "#ff5555"
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

def estrategia_suporte_resistencia(df):
    u = df.iloc[-1]; sinal, cor = "⏳ AGUARDAR", "yellow"
    sup, res = detectar_niveis_h1(PAR)
    margem = u['close'] * 0.0001
    for s in sup:
        if abs(u['close'] - s) <= margem: sinal, cor = "📈 CALL SUP", "#00ffff"; break
    if "AGUARDAR" in sinal:
        for r in res:
            if abs(u['close'] - r) <= margem: sinal, cor = "📉 PUT RES", "#ff00ff"; break
    return sinal, cor, calcular_forca_vela(df), medir_confluencia_total(df, sinal)

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

# ================= MOTOR DE ANÁLISE =================
def analisar():
    global rodando
    while rodando:
        try:
            txt_nws, cor_nws = verificar_status_mercado()
            root.after(0, lambda: news_label.config(text=txt_nws, fg=cor_nws))

            data = yf.download(PAR, period="5d", interval=TIMEFRAME, progress=False)
            if data is not None and not data.empty:
                df = data.copy()
                df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

                df['rsi'] = ta.momentum.RSIIndicator(df['close'], CONFIG["RSI_PERIODO"]).rsi()
                df['ema9'] = ta.trend.EMAIndicator(df['close'], CONFIG["EMA_CURTA"]).ema_indicator()
                df['ema21'] = ta.trend.EMAIndicator(df['close'], CONFIG["EMA_LONGA"]).ema_indicator()
                df['ema_trend'] = ta.trend.EMAIndicator(df['close'], CONFIG["EMA_TENDENCIA"]).ema_indicator()
                df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], CONFIG["ADX_PERIODO"]).adx()
                df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close'], CONFIG["CCI_PERIODO"]).cci()
                bb = ta.volatility.BollingerBands(df['close'], window=CONFIG["BB_PERIODO"], window_dev=CONFIG["BB_DESVIO"])
                df['bb_high'], df['bb_low'] = bb.bollinger_hband(), bb.bollinger_lband()
                stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'], window=CONFIG["STOCH_K"], smooth_window=CONFIG["STOCH_D"])
                df['stoch_k'], df['stoch_d'] = stoch.stoch(), stoch.stoch_signal()
                macd = ta.trend.MACD(df['close'], window_fast=CONFIG["MACD_FAST"], window_slow=CONFIG["MACD_SLOW"])
                df['macd_val'], df['macd_signal'] = macd.macd(), macd.macd_signal()

                df.dropna(inplace=True)
                if not df.empty:
                    sinal, cor, f_v, f_s = ESTRATEGIAS[ESTRATEGIA](df)
                    
                    # --- NOVOS FILTROS (TÓPICO 2) ---
                    t_h1 = verificar_tendencia_macro(PAR)
                    # atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range().iloc[-1]
                    
                    # Filtro de Tendência Global
                    if "CALL" in sinal and t_h1 == "BAIXA":
                        sinal, cor = "⏳ AGUARDAR (H1 Baixa)", "gray"
                    elif "PUT" in sinal and t_h1 == "ALTA":
                        sinal, cor = "⏳ AGUARDAR (H1 Alta)", "gray"
                    
                    # # Filtro de Volatilidade (ATR Mínimo)
                    # if atr < (df['close'].iloc[-1] * 0.00005):
                    #     sinal, cor = "⏳ SEM VOLATILIDADE", "#444"

                    # root.after(0, atualizar_sinal, sinal, cor, f_v, f_s)
                    # if "📈" in sinal or "📉" in sinal:
                    #     winsound.Beep(1000, 500)
                    #     reg = f"{datetime.now().strftime('%H:%M:%S')} | {sinal} | Conf: {f_s}%"
                    #     root.after(0, lambda r=reg: adicionar_historico(r))

            for i in range(30, 0, -1):
                if not rodando: break
                root.after(0, lambda t=i: tempo_label.config(text=f"⏱ Próxima Análise: {t}s"))
                time.sleep(1)
        except Exception as e:
            print(f"Erro: {e}"); time.sleep(5)

# ================= FUNÇÕES DE CONTROLE =================
# def registrar_resultado(tipo):
#     global PLACAR
#     PLACAR[tipo] += 1
#     total = PLACAR["WIN"] + PLACAR["LOSS"]
#     wr = (PLACAR["WIN"] / total * 100) if total > 0 else 0
#     placar_label.config(text=f"🏆 WIN: {PLACAR['WIN']} | ❌ LOSS: {PLACAR['LOSS']} ({wr:.1f}%)")

def aplicar_config():
    global PAR, TIMEFRAME, EXPIRACAO, ESTRATEGIA, CONFIG
    try:
        PAR = par_var.get(); TIMEFRAME = tf_var.get(); EXPIRACAO = int(exp_var.get()); ESTRATEGIA = est_var.get()
        CONFIG["RSI_PERIODO"] = int(rsi_p_var.get()); CONFIG["RSI_UPPER"] = int(rsi_u_var.get()); CONFIG["RSI_LOWER"] = int(rsi_l_var.get())
        CONFIG["EMA_CURTA"] = int(ema_c_var.get()); CONFIG["EMA_LONGA"] = int(ema_l_var.get()); CONFIG["EMA_TENDENCIA"] = int(ema_t_var.get())
        CONFIG["ADX_PERIODO"] = int(adx_p_var.get()); CONFIG["ADX_MINIMO"] = int(adx_m_var.get())
        CONFIG["CCI_PERIODO"] = int(cci_p_var.get()); CONFIG["CCI_EXTREMO"] = int(cci_e_var.get())
        CONFIG["BB_PERIODO"] = int(bb_p_var.get()); CONFIG["BB_DESVIO"] = float(bb_d_var.get())
        CONFIG["STOCH_K"] = int(st_k_var.get()); CONFIG["STOCH_D"] = int(st_d_var.get())
        CONFIG["MACD_FAST"] = int(mc_f_var.get()); CONFIG["MACD_SLOW"] = int(mc_s_var.get())
        status_label.config(text=f"✅ SISTEMA CALIBRADO", fg="cyan")
    except Exception as e:
        status_label.config(text=f"Erro: {e}", fg="red")

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        threading.Thread(target=analisar, daemon=True).start()
        sinal_label.config(text="▶ AGUARDANDO...", fg="white")

def parar():
    global rodando
    rodando = False
    sinal_label.config(text="⏹️ PARADO", fg="white")

def limpar_historico():
    historico_box.delete(0, END)

def atualizar_sinal(sinal, cor, f_v, f_s):
    sinal_label.config(text=sinal, fg=cor)
    forca_vela_label.config(text=f"Vela: {f_v}%", fg="green" if f_v>=60 else "yellow")
    forca_sinal_label.config(text=f"Confiança: {f_s}%", fg="green" if f_s>=75 else "yellow")
    par_label.config(text=f"{PAR} | {TIMEFRAME.upper()} | EXP {EXPIRACAO}m")

def adicionar_historico(texto):
    historico_box.insert(0, texto)
    if historico_box.size() > 50: historico_box.delete(50)

# ================= INTERFACE OTIMIZADA =================
root = Tk()
root.title("Rafiki Trader PRO")
root.geometry("600x650") 
root.configure(bg="#0d0d0d")

news_frame = Frame(root, bg="#222", height=30)
news_frame.pack(fill="x", padx=10, pady=2)
news_label = Label(news_frame, text="VERIFICANDO...", fg="#00ff00", bg="#222", font=("Arial", 9, "bold"))
news_label.pack()

Label(root, text="RAFIKI TRADER ENGINE", fg="cyan", bg="#0d0d0d", font=("Arial",14,"bold")).pack(pady=2)
status_label = Label(root, text="Calibre e inicie", fg="white", bg="#0d0d0d", font=("Arial", 9))
status_label.pack()

# --- ATIVOS ---
f_ativo = LabelFrame(root, text=" Configuração ", fg="yellow", bg="#0d0d0d", padx=5, pady=5)
f_ativo.pack(pady=2, fill="x", padx=10)
par_var = StringVar(value=PAR); Entry(f_ativo, textvariable=par_var, width=10).grid(row=0, column=1)
Label(f_ativo, text="Par:", fg="white", bg="#0d0d0d").grid(row=0, column=0)
tf_var = StringVar(value=TIMEFRAME); ttk.Combobox(f_ativo, textvariable=tf_var, values=TIMEFRAMES_YF, width=5).grid(row=0, column=3)
Label(f_ativo, text=" TF:", fg="white", bg="#0d0d0d").grid(row=0, column=2)
est_var = StringVar(value=ESTRATEGIA); ttk.Combobox(f_ativo, textvariable=est_var, values=list(ESTRATEGIAS.keys()), width=15).grid(row=0, column=5)
Label(f_ativo, text=" Estratégia:", fg="white", bg="#0d0d0d").grid(row=0, column=4)
exp_var = StringVar(value="1"); ttk.Combobox(f_ativo, textvariable=exp_var, values=EXPIRACOES, width=3).grid(row=0, column=7)
Label(f_ativo, text=" Exp:", fg="white", bg="#0d0d0d").grid(row=0, column=6)

# --- AJUSTES TÉCNICOS ---
f_tecnico = LabelFrame(root, text=" Painel Técnico ", fg="cyan", bg="#0d0d0d", padx=5, pady=5)
f_tecnico.pack(pady=2, fill="x", padx=10)
rsi_p_var = StringVar(value="14"); Entry(f_tecnico, textvariable=rsi_p_var, width=5).grid(row=0, column=1)
Label(f_tecnico, text="RSI Per:", fg="white", bg="#0d0d0d").grid(row=0, column=0, sticky="e")
rsi_u_var = StringVar(value="70"); Entry(f_tecnico, textvariable=rsi_u_var, width=5).grid(row=1, column=1)
Label(f_tecnico, text="RSI Up:", fg="white", bg="#0d0d0d").grid(row=1, column=0, sticky="e")
rsi_l_var = StringVar(value="30"); Entry(f_tecnico, textvariable=rsi_l_var, width=5).grid(row=2, column=1)
Label(f_tecnico, text="RSI Low:", fg="white", bg="#0d0d0d").grid(row=2, column=0, sticky="e")
adx_p_var = StringVar(value="14"); Entry(f_tecnico, textvariable=adx_p_var, width=5).grid(row=3, column=1)
Label(f_tecnico, text="ADX Per:", fg="white", bg="#0d0d0d").grid(row=3, column=0, sticky="e")
mc_f_var = StringVar(value="12"); Entry(f_tecnico, textvariable=mc_f_var, width=5).grid(row=4, column=1)
Label(f_tecnico, text="MACD F:", fg="white", bg="#0d0d0d").grid(row=4, column=0, sticky="e")
ema_c_var = StringVar(value="9"); Entry(f_tecnico, textvariable=ema_c_var, width=5).grid(row=0, column=3)
Label(f_tecnico, text=" EMA Curta:", fg="white", bg="#0d0d0d").grid(row=0, column=2, sticky="e")
ema_l_var = StringVar(value="21"); Entry(f_tecnico, textvariable=ema_l_var, width=5).grid(row=1, column=3)
Label(f_tecnico, text=" EMA Longa:", fg="white", bg="#0d0d0d").grid(row=1, column=2, sticky="e")
ema_t_var = StringVar(value="100"); Entry(f_tecnico, textvariable=ema_t_var, width=5).grid(row=2, column=3)
Label(f_tecnico, text=" EMA Trend:", fg="white", bg="#0d0d0d").grid(row=2, column=2, sticky="e")
adx_m_var = StringVar(value="25"); Entry(f_tecnico, textvariable=adx_m_var, width=5).grid(row=3, column=3)
Label(f_tecnico, text=" ADX Mín:", fg="white", bg="#0d0d0d").grid(row=3, column=2, sticky="e")
mc_s_var = StringVar(value="26"); Entry(f_tecnico, textvariable=mc_s_var, width=5).grid(row=4, column=3)
Label(f_tecnico, text=" MACD S:", fg="white", bg="#0d0d0d").grid(row=4, column=2, sticky="e")
cci_p_var = StringVar(value="20"); Entry(f_tecnico, textvariable=cci_p_var, width=5).grid(row=0, column=5)
Label(f_tecnico, text=" CCI Per:", fg="white", bg="#0d0d0d").grid(row=0, column=4, sticky="e")
cci_e_var = StringVar(value="100"); Entry(f_tecnico, textvariable=cci_e_var, width=5).grid(row=1, column=5)
Label(f_tecnico, text=" CCI Extr:", fg="white", bg="#0d0d0d").grid(row=1, column=4, sticky="e")
bb_p_var = StringVar(value="20"); Entry(f_tecnico, textvariable=bb_p_var, width=5).grid(row=2, column=5)
Label(f_tecnico, text=" BB Per:", fg="white", bg="#0d0d0d").grid(row=2, column=4, sticky="e")
bb_d_var = StringVar(value="2"); Entry(f_tecnico, textvariable=bb_d_var, width=5).grid(row=3, column=5)
Label(f_tecnico, text=" BB Desv:", fg="white", bg="#0d0d0d").grid(row=3, column=4, sticky="e")
st_k_var = StringVar(value="14"); st_d_var = StringVar(value="3")
Entry(f_tecnico, textvariable=st_k_var, width=2).grid(row=4, column=5, sticky="w")
Entry(f_tecnico, textvariable=st_d_var, width=2).grid(row=4, column=5, sticky="e")
Label(f_tecnico, text=" Stoch K/D:", fg="white", bg="#0d0d0d").grid(row=4, column=4, sticky="e")

Button(root, text="🔄 APLICAR TUDO", command=aplicar_config, bg="#333", fg="white", font=("Arial", 9, "bold")).pack(pady=5, fill="x", padx=50)

# --- NOVO: PAINEL DE PLACAR (TÓPICO 4) ---
# f_placar = Frame(root, bg="#111", pady=5)
# f_placar.pack(fill="x", padx=10, pady=5)
# placar_label = Label(f_placar, text="🏆 WIN: 0 | ❌ LOSS: 0 (0.0%)", fg="white", bg="#111", font=("Arial", 10, "bold"))
# placar_label.pack()
# btn_placar_f = Frame(f_placar, bg="#111")
# btn_placar_f.pack()
# Button(btn_placar_f, text="✅ WIN", command=lambda: registrar_resultado("WIN"), bg="#005500", fg="white", width=10).grid(row=0, column=0, padx=5)
# Button(btn_placar_f, text="❌ LOSS", command=lambda: registrar_resultado("LOSS"), bg="#550000", fg="white", width=10).grid(row=0, column=1, padx=5)

# --- RESULTADOS ---
sinal_label = Label(root, text="---", fg="white", bg="#0d0d0d", font=("Arial", 26, "bold")); sinal_label.pack()
f_info = Frame(root, bg="#0d0d0d")
f_info.pack()
forca_vela_label = Label(f_info, text="Vela: 0%", fg="#888", bg="#0d0d0d", font=("Arial", 11, "bold")); forca_vela_label.grid(row=0, column=0, padx=10)
forca_sinal_label = Label(f_info, text="Confiança: 0%", fg="#888", bg="#0d0d0d", font=("Arial", 11, "bold")); forca_sinal_label.grid(row=0, column=1, padx=10)

tempo_label = Label(root, text="⏱ 0s", fg="yellow", bg="#0d0d0d", font=("Arial", 10)); tempo_label.pack()
par_label = Label(root, text="---", fg="cyan", bg="#0d0d0d", font=("Arial", 9)); par_label.pack()

historico_box = Listbox(root, width=65, height=5, bg="#111", fg="white", font=("Consolas", 9)); historico_box.pack(pady=5)
Button(root, text="LIMPAR LOG", command=limpar_historico, bg="#222", fg="#888", font=("Arial", 7)).pack()

# --- CONTROLES ---
btn_f = Frame(root, bg="#0d0d0d")
btn_f.pack(pady=10)
Button(btn_f, text="▶ INICIAR MOTOR", command=iniciar, bg="#00aa88", width=18, font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10)
Button(btn_f, text="■ PARAR MOTOR", command=parar, bg="#aa3333", width=18, fg="white", font=("Arial", 11, "bold")).grid(row=0, column=1, padx=10)


root.mainloop()

