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

TIMEFRAMES_YF = ["1m","2m","5m","15m","30m","60m","90m","1d","5d","1wk","1mo"]
EXPIRACOES = list(range(1,31))

LINHAS_MAPA = [
    ["Sniper Precisão", "Bollinger + RSI + EMA Trend + ADX. Reversão técnica."],
    ["CCI Reversa", "Exaustão de preço via Commodity Channel Index."],
    ["RSI + EMA", "Cruzamento de médias curtas filtrado por RSI."],
    ["EMA Trend", "Seguir tendência das médias móveis e momentum RSI."],
    ["RSI Extremo", "Entradas em zonas de Sobrecompra (70) e Sobrevenda (30)."],
    ["MACD", "Cruzamento da linha de sinal do MACD."],
    ["Confluência PRO", "Múltiplos indicadores apontando para a mesma direção."],
    ["Bollinger Bands", "Preço tocando as extremidades das Bandas."],
    ["Stochastic", "Cruzamento das linhas %K e %D do Estocástico."],
    ["Suporte/Resistência", "Ação do preço próxima a fundos e topos recentes de H1."]
]

# ================= NOVO: DETECÇÃO DE PREÇO H1 =================
def detectar_niveis_h1(par):
    try:
        # Baixa dados de 1 hora para achar regiões de memória do mercado
        data_h1 = yf.download(par, period="5d", interval="60m", progress=False)
        if data_h1.empty: return [], []
        
        if isinstance(data_h1.columns, pd.MultiIndex):
            data_h1.columns = [c[0].lower() for c in data_h1.columns]
        else:
            data_h1.columns = [c.lower() for c in data_h1.columns]

        # Pegamos os 5 maiores topos e 5 menores fundos recentes
        resistencias = data_h1['high'].nlargest(5).tolist()
        suportes = data_h1['low'].nsmallest(5).tolist()
        return suportes, resistencias
    except:
        return [], []

# ================= UTILIDADES =================
def calcular_forca_vela(df):
    try:
        u = df.iloc[-1]
        if abs(u['high'] - u['low']) < 0.000001:
            u = df.iloc[-2] if len(df) > 1 else u
            
        corpo = abs(u['close'] - u['open'])
        range_total = u['high'] - u['low']

        if range_total < 0.000001:
            return round(abs(50 - u['rsi']) * 2, 1)

        forca = (corpo / range_total) * 100
        return round(min(forca, 100), 1)
    except:
        return 50.0

def calcular_forca_sinal(sinal_tipo, forca_vela, rsi=50, adx=0):
    if "AGUARDAR" in sinal_tipo: return 0
    p1 = forca_vela * 0.3
    dist_extrema = abs(50 - rsi)
    p2 = (dist_extrema / 50) * 40
    p3 = (adx / 100) * 30
    noise = random.uniform(0.1, 0.9)
    total = round(p1 + p2 + p3 + noise, 1)
    return max(min(total, 100), 15.0)

# ================= ESTRATÉGIAS =================
def estrategia_sniper_pro(df):
    u = df.iloc[-1]
    tendencia_alta = u['close'] > u['ema_trend']
    tendencia_baixa = u['close'] < u['ema_trend']
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['close'] <= u['bb_low'] and u['rsi'] < 30 and tendencia_alta and u['adx'] > CONFIG["ADX_MINIMO"]:
        sinal, cor = "📈 CALL SNIPER", "#00ff99"
    elif u['close'] >= u['bb_high'] and u['rsi'] > 70 and tendencia_baixa and u['adx'] > CONFIG["ADX_MINIMO"]:
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
    a, u = df.iloc[-2], df.iloc[-1]; fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['macd_val'] < a['macd_signal'] and u['macd_val'] > u['macd_signal']: sinal, cor = "📈 CALL", "#00ff99"
    elif a['macd_val'] > a['macd_signal'] and u['macd_val'] < u['macd_signal']: sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_confluencia(df):
    u = df.iloc[-1]; fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['ema9'] > u['ema21'] and 40 < u['rsi'] < 55: sinal, cor = "📈 CALL", "#00ffaa"
    elif u['ema9'] < u['ema21'] and 45 < u['rsi'] < 60: sinal, cor = "📉 PUT", "#ff6666"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_bollinger(df):
    u = df.iloc[-1]; fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if u['close'] < u['bb_low']: sinal, cor = "📈 CALL", "#00ff99"
    elif u['close'] > u['bb_high']: sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

def estrategia_stochastic(df):
    u, a = df.iloc[-1], df.iloc[-2]; fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    if a['stoch_k'] < a['stoch_d'] and u['stoch_k'] > u['stoch_d']: sinal, cor = "📈 CALL", "#00ff99"
    elif a['stoch_k'] > a['stoch_d'] and u['stoch_k'] < u['stoch_d']: sinal, cor = "📉 PUT", "#ff5555"
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

# NOVO: ESTRATÉGIA SUPORTE/RESISTÊNCIA COM FILTRO H1
def estrategia_suporte_resistencia(df):
    u = df.iloc[-1]
    fv = calcular_forca_vela(df)
    sinal, cor = "⏳ AGUARDAR", "yellow"
    
    suportes_h1, resistencias_h1 = detectar_niveis_h1(PAR)
    # Tolerância de 0.01% para considerar que "tocou" na linha
    margem = u['close'] * 0.0001 
    
    for sup in suportes_h1:
        if abs(u['close'] - sup) <= margem:
            if u['rsi'] < 35:
                sinal, cor = "📈 CALL SR-H1", "#00ffff"
                break
    
    if "AGUARDAR" in sinal:
        for res in resistencias_h1:
            if abs(u['close'] - res) <= margem:
                if u['rsi'] > 65:
                    sinal, cor = "📉 PUT SR-H1", "#ff00ff"
                    break
                    
    return sinal, cor, fv, calcular_forca_sinal(sinal, fv, u['rsi'], adx=u['adx'])

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
            agora = datetime.now()
            data = yf.download(PAR, period="5d", interval=TIMEFRAME, progress=False)
            
            if data is not None and not data.empty:
                df = data.copy()
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0].lower() for c in df.columns]
                else:
                    df.columns = [c.lower() for c in df.columns]
                
                df = df[['open', 'high', 'low', 'close']]
                
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
                    root.after(0, atualizar_sinal, sinal, cor, f_v, f_s)
                    
                    if "AGUARDAR" not in sinal:
                        winsound.Beep(1000, 500)
                        registro = f"{agora.strftime('%H:%M:%S')} | {sinal} | Força: {f_s}%"
                        root.after(0, lambda reg=registro: adicionar_historico(reg))
            
            for i in range(30, 0, -1):
                if not rodando: break
                root.after(0, lambda t=i: tempo_label.config(text=f"⏱ Próxima Análise: {t}s"))
                time.sleep(1)
                
        except Exception as e:
            print(f"Erro no Motor: {e}")
            time.sleep(5)

# ================= FUNÇÕES DE CONTROLE =================
def aplicar_config():
    global PAR, TIMEFRAME, EXPIRACAO, ESTRATEGIA, CONFIG
    try:
        PAR = par_var.get()
        TIMEFRAME = tf_var.get()
        EXPIRACAO = int(exp_var.get())
        ESTRATEGIA = est_var.get()
        
        CONFIG["RSI_PERIODO"] = int(rsi_p_var.get())
        CONFIG["EMA_CURTA"] = int(ema_c_var.get())
        CONFIG["EMA_LONGA"] = int(ema_l_var.get())
        CONFIG["EMA_TENDENCIA"] = int(ema_t_var.get())
        CONFIG["ADX_PERIODO"] = int(adx_p_var.get())
        CONFIG["ADX_MINIMO"] = int(adx_m_var.get())
        CONFIG["CCI_EXTREMO"] = int(cci_e_var.get())
        CONFIG["BB_PERIODO"] = int(bb_p_var.get())
        CONFIG["BB_DESVIO"] = int(bb_d_var.get())
        CONFIG["STOCH_K"] = int(st_k_var.get())
        CONFIG["STOCH_D"] = int(st_d_var.get())
        CONFIG["MACD_FAST"] = int(mc_f_var.get())
        CONFIG["MACD_SLOW"] = int(mc_s_var.get())
        
        status_label.config(text=f"CONFIGURADO: {PAR} | {TIMEFRAME}", fg="cyan")
    except:
        status_label.config(text="Erro nos valores numéricos", fg="red")

def iniciar():
    global rodando
    if not rodando:
        rodando = True
        threading.Thread(target=analisar, daemon=True).start()
        sinal_label.config(text="▶ Rodando...", fg="white")

def parar():
    global rodando
    rodando = False
    sinal_label.config(text="⏹️ Parado", fg="white")

def limpar_historico():
    historico_box.delete(0, END)

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
root.geometry("680x950")
root.configure(bg="#0d0d0d")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

frame_trader = Frame(notebook, bg="#0d0d0d")
notebook.add(frame_trader, text="Trader")

Label(frame_trader, text="RAFIKI TRADER PRO", fg="cyan", bg="#0d0d0d", font=("Arial",16,"bold")).pack(pady=5)
status_label = Label(frame_trader, text="Configure e clique em Aplicar", fg="white", bg="#0d0d0d")
status_label.pack()

# --- ATIVOS ---
f_ativo = LabelFrame(frame_trader, text=" Ativo e Estratégia ", fg="yellow", bg="#0d0d0d", padx=10, pady=5)
f_ativo.pack(pady=5, fill="x", padx=20)

par_var = StringVar(value=PAR); Entry(f_ativo, textvariable=par_var, width=12).grid(row=0, column=1)
Label(f_ativo, text="Par:", fg="white", bg="#0d0d0d").grid(row=0, column=0)
tf_var = StringVar(value=TIMEFRAME); ttk.Combobox(f_ativo, textvariable=tf_var, values=TIMEFRAMES_YF, width=8).grid(row=0, column=3)
Label(f_ativo, text=" TF:", fg="white", bg="#0d0d0d").grid(row=0, column=2)
est_var = StringVar(value=ESTRATEGIA); ttk.Combobox(f_ativo, textvariable=est_var, values=list(ESTRATEGIAS.keys()), width=18).grid(row=1, column=1, pady=5)
Label(f_ativo, text="Estratégia:", fg="white", bg="#0d0d0d").grid(row=1, column=0)
exp_var = StringVar(value="1"); ttk.Combobox(f_ativo, textvariable=exp_var, values=EXPIRACOES, width=5).grid(row=1, column=3)
Label(f_ativo, text=" Exp:", fg="white", bg="#0d0d0d").grid(row=1, column=2)

# --- AJUSTES TÉCNICOS ---
f_tecnico = LabelFrame(frame_trader, text=" Ajustes Técnicos dos Indicadores ", fg="cyan", bg="#0d0d0d", padx=10, pady=10)
f_tecnico.pack(pady=5, fill="x", padx=20)

rsi_p_var = StringVar(value="14"); Entry(f_tecnico, textvariable=rsi_p_var, width=5).grid(row=0, column=1)
Label(f_tecnico, text="RSI Per:", fg="white", bg="#0d0d0d").grid(row=0, column=0, sticky="w")
ema_c_var = StringVar(value="9"); Entry(f_tecnico, textvariable=ema_c_var, width=5).grid(row=0, column=3)
Label(f_tecnico, text=" EMA Curta:", fg="white", bg="#0d0d0d").grid(row=0, column=2, sticky="w")
ema_l_var = StringVar(value="21"); Entry(f_tecnico, textvariable=ema_l_var, width=5).grid(row=0, column=5)
Label(f_tecnico, text=" EMA Longa:", fg="white", bg="#0d0d0d").grid(row=0, column=4, sticky="w")

adx_p_var = StringVar(value="14"); Entry(f_tecnico, textvariable=adx_p_var, width=5).grid(row=1, column=1, pady=5)
Label(f_tecnico, text="ADX Per:", fg="white", bg="#0d0d0d").grid(row=1, column=0, sticky="w")
adx_m_var = StringVar(value="25"); Entry(f_tecnico, textvariable=adx_m_var, width=5).grid(row=1, column=3)
Label(f_tecnico, text=" ADX Mín:", fg="white", bg="#0d0d0d").grid(row=1, column=2, sticky="w")
ema_t_var = StringVar(value="100"); Entry(f_tecnico, textvariable=ema_t_var, width=5).grid(row=1, column=5)
Label(f_tecnico, text=" EMA Trend:", fg="white", bg="#0d0d0d").grid(row=1, column=4, sticky="w")

bb_p_var = StringVar(value="20"); Entry(f_tecnico, textvariable=bb_p_var, width=5).grid(row=2, column=1)
Label(f_tecnico, text="BB Per:", fg="white", bg="#0d0d0d").grid(row=2, column=0, sticky="w")
bb_d_var = StringVar(value="2"); Entry(f_tecnico, textvariable=bb_d_var, width=5).grid(row=2, column=3)
Label(f_tecnico, text=" BB Desvio:", fg="white", bg="#0d0d0d").grid(row=2, column=2, sticky="w")
cci_e_var = StringVar(value="100"); Entry(f_tecnico, textvariable=cci_e_var, width=5).grid(row=2, column=5)
Label(f_tecnico, text=" CCI Extr:", fg="white", bg="#0d0d0d").grid(row=2, column=4, sticky="w")

st_k_var = StringVar(value="14"); Entry(f_tecnico, textvariable=st_k_var, width=5).grid(row=3, column=1, pady=5)
Label(f_tecnico, text="Stoch K:", fg="white", bg="#0d0d0d").grid(row=3, column=0, sticky="w")
st_d_var = StringVar(value="3"); Entry(f_tecnico, textvariable=st_d_var, width=5).grid(row=3, column=3)
Label(f_tecnico, text=" Stoch D:", fg="white", bg="#0d0d0d").grid(row=3, column=2, sticky="w")
mc_f_var = StringVar(value="12"); Entry(f_tecnico, textvariable=mc_f_var, width=5).grid(row=4, column=1)
Label(f_tecnico, text="MACD Fast:", fg="white", bg="#0d0d0d").grid(row=4, column=0, sticky="w")
mc_s_var = StringVar(value="26"); Entry(f_tecnico, textvariable=mc_s_var, width=5).grid(row=4, column=3)
Label(f_tecnico, text=" MACD Slow:", fg="white", bg="#0d0d0d").grid(row=4, column=2, sticky="w")

Button(frame_trader, text="🔄 APLICAR TUDO", command=aplicar_config, bg="#444", fg="white", font=("Arial", 10, "bold")).pack(pady=10, fill="x", padx=40)

# --- RESULTADOS ---
sinal_label = Label(frame_trader, text="---", fg="white", bg="#0d0d0d", font=("Arial", 22, "bold")); sinal_label.pack()
f_info = Frame(frame_trader, bg="#0d0d0d")
f_info.pack(pady=5)
forca_vela_label = Label(f_info, text="Força Vela: 0.0%", fg="white", bg="#0d0d0d", font=("Arial", 12, "bold")); forca_vela_label.grid(row=0, column=0, padx=10)
forca_sinal_label = Label(f_info, text="Força Sinal: 0.0%", fg="white", bg="#0d0d0d", font=("Arial", 12, "bold")); forca_sinal_label.grid(row=0, column=1, padx=10)
tempo_label = Label(frame_trader, text="⏱ 0s", fg="yellow", bg="#0d0d0d", font=("Arial", 12)); tempo_label.pack()
par_label = Label(frame_trader, text="---", fg="cyan", bg="#0d0d0d"); par_label.pack()

historico_box = Listbox(frame_trader, width=70, height=6, bg="#111", fg="white"); historico_box.pack(pady=10)
Button(frame_trader, text="🧹 Limpar Histórico", command=limpar_historico, bg="#222", fg="gray", font=("Arial", 8)).pack()

btn_f = Frame(frame_trader, bg="#0d0d0d")
btn_f.pack(pady=10)
Button(btn_f, text="▶ INICIAR", command=iniciar, bg="#00aa88", width=20, font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5)
Button(btn_f, text="■ PARAR", command=parar, bg="#aa3333", width=20, fg="white", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5)

# --- MAPA ---
frame_mapa = Frame(notebook, bg="#0d0d0d")
notebook.add(frame_mapa, text="Mapa de Estratégias")
tabela_frame = Frame(frame_mapa, bg="#0d0d0d")
tabela_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

for r, linha in enumerate(LINHAS_MAPA):
    for c, valor in enumerate(linha):
        Label(tabela_frame, text=valor, fg="white", bg="#111", borderwidth=1, relief="solid", wraplength=300).grid(row=r, column=c, sticky="nsew")

root.mainloop()
