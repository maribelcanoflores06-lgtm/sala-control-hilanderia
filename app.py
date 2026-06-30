# =============================================================================
# SALA DE CONTROL · HILANDERÍA
# Dashboard de estado y eficiencia de máquinas continuas de anillo
# Autor: Maribel Cano
# =============================================================================

import streamlit as st
import pandas as pd
import re
import unicodedata
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Sala de Control · Hilandería",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# ESTILOS (CSS del panel de control oscuro estilo industrial)
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* --- Variables de color --- */
:root {
  --bg:      #0B0F14;   /* fondo principal */
  --panel:   #121922;   /* fondo de tarjetas */
  --panel2:  #161E29;   /* fondo interior del anillo */
  --line:    #232E3B;   /* bordes */
  --text:    #E8EDF2;   /* texto principal */
  --text2:   #7C8A99;   /* texto secundario */
  --ok:      #3DDC84;   /* verde: operando */
  --ok-dim:  #1E5E3E;
  --warn:    #F5A623;   /* ámbar: eficiencia media */
  --warn-dim:#5B4419;
  --bad:     #E2424D;   /* rojo: parada */
  --bad-dim: #5A2025;
}

/* --- Layout general --- */
.stApp { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; }
[data-testid="stHeader"] { background: var(--bg); }
.block-container { padding-top: 1rem; max-width: 1500px; }

/* --- Barra superior con KPIs --- */
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px 20px; margin-bottom: 14px;
}
.topbar h1 {
  font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 22px;
  margin: 0; letter-spacing: 1px; display: flex; align-items: center; gap: 10px;
}
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--ok); display: inline-block; box-shadow: 0 0 8px var(--ok); }
.kpi-row { display: flex; gap: 28px; align-items: center; }
.kpi { text-align: center; }
.kpi .num { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; }
.kpi .lbl { font-size: 10px; color: var(--text2); letter-spacing: 1px; }
.kpi.ok  .num { color: var(--ok); }
.kpi.bad .num { color: var(--bad); }
.kpi.warn .num { color: var(--warn); }

/* --- Ticker de alarmas animado --- */
.alarm-bar {
  background: var(--bad-dim); border: 1px solid var(--bad); border-radius: 8px;
  padding: 8px 16px; margin-bottom: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px; color: #ffd9dc;
  overflow: hidden; white-space: nowrap;
}
.ticker-track {
  display: inline-block;
  animation: ticker-scroll 30s linear infinite;
}
@keyframes ticker-scroll {
  0%   { transform: translateX(100vw); }
  100% { transform: translateX(-100%); }
}

/* --- Tarjetas de máquina --- */
.card {
  background: var(--panel); border: 1px solid var(--line);
  border-left: 4px solid var(--line); border-radius: 10px;
  padding: 14px 16px 36px 16px; margin-bottom: 14px;
  min-height: 150px; position: relative;
}
.card.ok  { border-left-color: var(--ok); }
.card.bad { border-left-color: var(--bad); }

.card-head  { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2px; }
.card-title { font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 18px; }
.card-turno { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text2); font-weight: 600; }
.card-sub   { font-size: 11px; color: var(--text2); margin-top: -2px; margin-bottom: 8px; }

.badge     { font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 5px; letter-spacing: 0.5px; }
.badge.ok  { background: var(--ok-dim);  color: var(--ok); }
.badge.bad { background: var(--bad-dim); color: var(--bad); }

.metrics   { display: flex; gap: 18px; margin-top: 8px; }
.metric .v { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 15px; }
.metric .l { font-size: 9px; color: var(--text2); letter-spacing: 0.5px; }

.stop-reason { color: var(--bad);   font-size: 12px; font-weight: 600; margin-top: 4px; }
.stop-since  { color: var(--text2); font-size: 11px; }

/* --- Anillo de eficiencia progresivo --- */
.ring-wrap  { position: relative; width: 62px; height: 62px; flex-shrink: 0; }
.ring-outer { width: 62px; height: 62px; border-radius: 50%; }
.ring-inner {
  position: absolute; top: 7px; left: 7px;
  width: 48px; height: 48px; border-radius: 50%;
  background: var(--panel2);
  display: flex; align-items: center; justify-content: center;
  font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 16px;
}

/* --- Botón lupa (esquina inferior derecha de la tarjeta) --- */
div[data-testid="stButton"] {
  margin-top: -34px; margin-bottom: 14px;
  display: flex; justify-content: flex-end; padding-right: 10px;
  position: relative; z-index: 10;
}
div[data-testid="stButton"] > button {
  width: 26px; height: 26px; min-height: 26px;
  border-radius: 50%; background: rgba(30,42,56,0.95);
  border: 1px solid #2D3E50; color: #5a8fa8;
  font-size: 13px; padding: 0; line-height: 1; cursor: pointer;
}
div[data-testid="stButton"] > button:hover {
  background: rgba(79,163,209,0.25); border-color: #4FA3D1; color: #7FC4FF;
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

# Nombres de columnas esperados en el archivo de producción
COLS_PROD = ['huso', 'maquina', 'dia', 'turno', 'hank', 'eficiencia',
             'velocidad', 'hr. producidas', 'hr. sin producir', 'codigo', 'titulo']

def normaliza_texto(c):
    """Limpia un texto: quita espacios, tildes, mayúsculas.
    Ejemplo: '  Día Prod ' → 'dia prod'
    """
    c = str(c).strip().lower()
    c = unicodedata.normalize('NFKD', c).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', c)


def busca_columna(df, candidatos):
    """Busca en el DataFrame la primera columna que coincida con alguno de los candidatos.
    Primero busca coincidencia exacta, luego coincidencia parcial.
    Retorna None si no encuentra nada.
    """
    cols = list(df.columns)
    # Coincidencia exacta
    for cand in candidatos:
        if cand in cols:
            return cand
    # Coincidencia parcial (el candidato está contenido en el nombre de la columna)
    for cand in candidatos:
        for col in cols:
            if cand in col:
                return col
    return None


def numero_maquina(nombre_archivo, df=None, col_maquina=None):
    """Extrae el número de máquina del nombre del archivo.
    Si no lo encuentra, lo lee del propio CSV.
    Ejemplo: 'Continua_N_5_junio_2026.csv' → 5
    """
    patron = re.search(r'(?:_N_|N°|N_|n_|maquina[_ ]?)(\d+)', nombre_archivo, re.IGNORECASE)
    if patron:
        return int(patron.group(1))
    if df is not None and col_maquina is not None and not df.empty:
        try:
            return int(df[col_maquina].dropna().iloc[0])
        except Exception:
            pass
    return None


def color_eficiencia(pct):
    """Define el color del anillo según el porcentaje de eficiencia:
    ≥85% → verde, ≥60% → ámbar, <60% → rojo, None → gris
    """
    if pct is None:    return 'grey'
    if pct >= 85:      return 'ok'
    if pct >= 60:      return 'warn'
    return 'bad'


def html_anillo(pct, clase_color):
    """Genera el HTML del anillo de eficiencia progresivo.
    Usa conic-gradient para llenar el arco proporcionalmente al %.
    """
    pct_val = 0 if pct is None else max(0, min(100, pct))
    colores = {'ok': '#3DDC84', 'warn': '#F5A623', 'bad': '#E2424D', 'grey': '#7C8A99'}
    color   = colores.get(clase_color, '#7C8A99')
    numero  = f"{int(pct_val)}" if pct is not None else "—"
    gradiente = f"conic-gradient({color} 0% {pct_val}%, #1e2a38 {pct_val}% 100%)"
    return (
        f'<div class="ring-wrap">'
        f'<div class="ring-outer" style="background:{gradiente};"></div>'
        f'<div class="ring-inner" style="color:{color};">{numero}</div>'
        f'</div>'
    )


def turno_a_numero(letra):
    """Convierte turno letra a número: A→1, B→2, C→3."""
    mapa = {'A': '1', 'B': '2', 'C': '3'}
    return mapa.get(str(letra).strip().upper()[:1], str(letra))


def turno_en_curso():
    """Detecta qué turno está corriendo ahora según la hora del sistema."""
    hora = datetime.now().hour
    if 7  <= hora < 15: return 'A'
    if 15 <= hora < 23: return 'B'
    return 'C'


def hora_inicio_turno(turno):
    """Retorna la hora de inicio de cada turno."""
    return {'A': 7, 'B': 15, 'C': 23}[turno]


def minutos_a_float(duracion_str):
    """Convierte una duración 'HH:MM:SS' a minutos decimales.
    Ejemplo: '01:30:00' → 90.0
    """
    try:
        h, m, s = str(duracion_str).split(':')
        return int(h) * 60 + int(m) + int(s) / 60
    except Exception:
        return None


def minutos_desde_hora(hhmmss):
    """Calcula cuántos minutos han pasado desde una hora 'HH:MM:SS' hasta ahora."""
    try:
        h, m, s = [int(x) for x in str(hhmmss).split(':')]
        ahora = datetime.now()
        ref   = ahora.replace(hour=h, minute=m, second=s, microsecond=0)
        diff  = (ahora - ref).total_seconds() / 60
        if diff < 0:
            diff += 24 * 60  # si la hora cruzó medianoche
        return int(diff)
    except Exception:
        return None


def limpia_texto(valor, fallback="Registrando..."):
    """Limpia valores inválidos (nan, None, vacíos) y retorna un texto limpio."""
    invalidos = {'nan', 'none', 'motivo no disponible', ''}
    if not valor or str(valor).strip().lower() in invalidos:
        return fallback
    return str(valor).strip()


def calcula_eficiencia_turno(df, col_dia, col_turno, col_inicio, col_fin, col_codigo, col_duracion):
    """Calcula la eficiencia del turno actual en tiempo real.

    Lógica: suma todos los minutos de 'Produccion' del turno actual
    y los divide entre los minutos transcurridos del turno.

    Retorna un porcentaje (0-100) o None si no hay datos.
    """
    ahora     = datetime.now()
    turno     = turno_en_curso()
    hoy       = pd.Timestamp(ahora.date())

    # Filtrar solo filas del turno actual y de hoy
    df_turno  = df[(df[col_dia] == hoy) &
                   (df[col_turno].astype(str).str.upper().str.startswith(turno))]
    if df_turno.empty:
        return None

    # Sumar minutos produciendo
    minutos_producidos = 0.0
    for _, fila in df_turno.iterrows():
        if str(fila[col_codigo]).strip() != '0':
            continue  # saltamos los paros, solo contamos producción
        fin_vacio = pd.isna(fila[col_fin]) or str(fila[col_fin]).strip() == ''
        if fin_vacio:
            # Tramo abierto: cuenta desde su inicio hasta ahora
            mins = minutos_desde_hora(fila[col_inicio])
            minutos_producidos += mins if mins else 0
        else:
            dur = minutos_a_float(fila[col_duracion])
            minutos_producidos += dur if dur else 0

    # Calcular minutos transcurridos del turno
    h_inicio       = hora_inicio_turno(turno)
    inicio_turno   = ahora.replace(hour=h_inicio, minute=0, second=0, microsecond=0)
    if turno == 'C' and ahora.hour < 7:
        inicio_turno -= pd.Timedelta(days=1)
    transcurridos = (ahora - inicio_turno).total_seconds() / 60

    if transcurridos <= 0:
        return None

    eficiencia = (minutos_producidos / transcurridos) * 100
    return round(max(0, min(100, eficiencia)), 1)


def lee_csv_produccion(archivo):
    """Lee un CSV de producción, detectando automáticamente si tiene encabezado o no.
    Retorna el DataFrame con columnas normalizadas.
    """
    # Detectar si la primera fila es encabezado o datos
    muestra       = pd.read_csv(archivo, nrows=1, header=None)
    archivo.seek(0)  # rebobinar el archivo para leerlo completo
    tiene_header  = str(muestra.iloc[0, 0]).strip().lower() == 'huso'

    df = pd.read_csv(archivo, header=0 if tiene_header else None)
    if not tiene_header:
        df.columns = COLS_PROD[:len(df.columns)]

    df.columns = [normaliza_texto(c) for c in df.columns]
    return df


def lee_csv_paros(archivo):
    """Lee un CSV de paros y retorna el DataFrame con columnas normalizadas."""
    df = pd.read_csv(archivo)
    df.columns = [normaliza_texto(c) for c in df.columns]
    return df


# =============================================================================
# CARGA DE ARCHIVOS
# =============================================================================
st.markdown("""
<div style="
  background: var(--panel);
  border: 1px solid var(--ok);
  border-left: 5px solid var(--ok);
  border-radius: 10px;
  padding: 18px 24px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 16px;
">
  <span style="width:14px;height:14px;border-radius:50%;background:var(--ok);
    box-shadow:0 0 14px var(--ok);display:inline-block;flex-shrink:0;"></span>
  <div>
    <div style="font-family:'Rajdhani',sans-serif;font-weight:700;font-size:30px;
      letter-spacing:4px;color:#FFFFFF;line-height:1;">
      SALA DE CONTROL · HILANDERÍA
    </div>
    <div style="font-size:11px;color:var(--ok);letter-spacing:3px;margin-top:4px;">
      MONITOREO DE MÁQUINAS EN TIEMPO REAL
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

with st.expander("📂 Cargar / actualizar archivos CSV",
                 expanded=not st.session_state.get('archivos_cargados', False)):
    col_izq, col_der = st.columns(2)
    with col_izq:
        archivos_prod = st.file_uploader(
            "Archivos de Producción (Continua_N_X...)",
            type="csv", accept_multiple_files=True, key="prod"
        )
    with col_der:
        archivos_paro = st.file_uploader(
            "Archivos de Paros (PARO_ORD_Continua_N_X...)",
            type="csv", accept_multiple_files=True, key="paro"
        )

if not archivos_prod or not archivos_paro:
    st.info("⬆️ Abre el panel de arriba para subir los archivos CSV de cada máquina.")
    st.stop()

st.session_state['archivos_cargados'] = True


# =============================================================================
# PROCESAMIENTO DE DATOS
# Leer todos los archivos y construir el diccionario de máquinas
# =============================================================================
maquinas = {}  # { numero_maquina: { datos... } }

# --- Archivos de producción ---
for archivo in archivos_prod:
    df = lee_csv_produccion(archivo)

    # Identificar columnas clave
    col_maq    = busca_columna(df, ['maquina'])
    col_dia    = busca_columna(df, ['dia'])
    col_turno  = busca_columna(df, ['turno'])
    col_eff    = busca_columna(df, ['eficiencia'])
    col_vel    = busca_columna(df, ['velocidad'])
    col_titulo = busca_columna(df, ['titulo'])
    col_hank   = busca_columna(df, ['hank'])

    if not all([col_maq, col_dia, col_turno, col_eff]):
        st.warning(f"⚠️ No reconocí las columnas de '{archivo.name}'. Lo omito.")
        continue

    df[col_dia] = pd.to_datetime(df[col_dia], format='%d/%m/%Y', errors='coerce')
    num = numero_maquina(archivo.name, df, col_maq)
    if num is None:
        st.warning(f"⚠️ No pude identificar el número de máquina en '{archivo.name}'.")
        continue

    # Buscar la fila del turno actual (para mostrar eficiencia en curso)
    hoy         = df[col_dia].max()
    df_hoy      = df[df[col_dia] == hoy]
    turno_hoy   = turno_en_curso()
    df_turno    = df_hoy[df_hoy[col_turno].astype(str).str.upper().str.startswith(turno_hoy)]
    fila        = df_turno.iloc[-1] if not df_turno.empty else (df_hoy.iloc[-1] if not df_hoy.empty else df.iloc[-1])

    maquinas.setdefault(num, {})
    maquinas[num]['turno']     = fila[col_turno]
    maquinas[num]['eficiencia'] = float(fila[col_eff]) if col_eff else None
    maquinas[num]['velocidad']  = float(fila[col_vel])    if col_vel    else None
    maquinas[num]['titulo']     = str(fila[col_titulo])   if col_titulo else None
    maquinas[num]['hank']       = float(fila[col_hank])   if col_hank   else None


# --- Archivos de paros ---
for archivo in archivos_paro:
    df = lee_csv_paros(archivo)

    col_maq      = busca_columna(df, ['num. maquina', 'num maquina', 'maquina'])
    col_dia      = busca_columna(df, ['dia'])
    col_turno    = busca_columna(df, ['turno'])
    col_inicio   = busca_columna(df, ['inicio'])
    col_fin      = busca_columna(df, ['fin'])
    col_duracion = busca_columna(df, ['duracion'])
    col_codigo   = busca_columna(df, ['codigo de paro', 'codigo'])
    col_motivo   = busca_columna(df, ['motivo de paro', 'motivo'])

    if not all([col_maq, col_dia, col_inicio, col_fin, col_codigo, col_motivo]):
        st.warning(f"⚠️ No reconocí las columnas de '{archivo.name}'. Lo omito.")
        continue

    df[col_dia] = pd.to_datetime(df[col_dia], format='%d/%m/%Y', errors='coerce')
    num = numero_maquina(archivo.name, df, col_maq)
    if num is None:
        st.warning(f"⚠️ No pude identificar el número de máquina en '{archivo.name}'.")
        continue

    # El estado actual está en la última fila (si Fin está vacío = sigue ocurriendo)
    ultima   = df.iloc[-1]
    fin_vacio = pd.isna(ultima[col_fin]) or str(ultima[col_fin]).strip() == ''
    codigo   = str(ultima[col_codigo]).strip()
    operando = fin_vacio and codigo == '0'

    maquinas.setdefault(num, {})
    maquinas[num]['operando']    = operando
    maquinas[num]['motivo']      = None if operando else str(ultima[col_motivo])
    maquinas[num]['desde']       = str(ultima[col_inicio])
    maquinas[num]['efic_turno']  = calcula_eficiencia_turno(
        df, col_dia, col_turno, col_inicio, col_fin, col_codigo, col_duracion
    )
    # Guardamos el DataFrame de paros para mostrarlo en el detalle
    maquinas[num]['df_paro']   = df
    maquinas[num]['cols_paro'] = {
        'dia': col_dia, 'turno': col_turno, 'inicio': col_inicio,
        'fin': col_fin, 'codigo': col_codigo, 'motivo': col_motivo, 'duracion': col_duracion
    }


# =============================================================================
# BARRA SUPERIOR (KPIs globales)
# =============================================================================
total      = len(maquinas)
operando_n = sum(1 for v in maquinas.values() if v.get('operando'))
paradas_n  = total - operando_n
efics      = [v['efic_turno'] for v in maquinas.values() if v.get('efic_turno') is not None]
efic_prom  = round(sum(efics) / len(efics), 1) if efics else 0
hora_ahora = datetime.now().strftime("%H:%M:%S")

st.markdown(
    f'<div class="topbar">'
    f'<h1><span class="dot"></span>FLOTA DE MÁQUINAS</h1>'
    f'<div class="kpi-row">'
    f'<div class="kpi ok"><div class="num">{operando_n}/{total}</div><div class="lbl">OPERANDO</div></div>'
    f'<div class="kpi bad"><div class="num">{paradas_n}</div><div class="lbl">PARADAS</div></div>'
    f'<div class="kpi warn"><div class="num">{efic_prom}%</div><div class="lbl">EFICIENCIA PROM.</div></div>'
    f'<div class="kpi"><div class="num">{hora_ahora}</div><div class="lbl">HORA LOCAL</div></div>'
    f'</div></div>',
    unsafe_allow_html=True
)


# =============================================================================
# TICKER DE ALARMAS (máquinas paradas con motivo conocido)
# =============================================================================
alarmas = []
for num, v in sorted(maquinas.items()):
    if v.get('operando'):
        continue
    motivo = limpia_texto(v.get('motivo', ''), fallback='')
    if not motivo:
        continue
    mins = minutos_desde_hora(v.get('desde'))
    texto = f"C-{num:02d} — {motivo}"
    if mins is not None:
        texto += f" · hace {mins} min"
    alarmas.append(texto)

if alarmas:
    separador = '&nbsp;&nbsp;&nbsp;&nbsp;⬥&nbsp;&nbsp;&nbsp;&nbsp;'
    contenido = separador.join(alarmas)
    st.markdown(
        f'<div class="alarm-bar">⚠️ ALARMAS RECIENTES&nbsp;&nbsp;&nbsp;'
        f'<span class="ticker-track">{contenido}&nbsp;&nbsp;&nbsp;&nbsp;{contenido}</span>'
        f'</div>',
        unsafe_allow_html=True
    )


# =============================================================================
# VENTANA DE DETALLE (se abre al hacer clic en la lupa 🔍)
# =============================================================================
def mostrar_detalle(num, v):
    """Muestra una ventana emergente con el detalle completo de la máquina."""

    def contenido():
        # Eficiencia del turno con anillo
        efic = v.get('efic_turno')
        clase = color_eficiencia(efic)
        st.markdown(html_anillo(efic, clase), unsafe_allow_html=True)
        efic_txt = f"{efic:.1f}%" if efic is not None else "—"
        st.markdown(f"**Eficiencia del turno: {efic_txt}**")

        # Estado y motivo
        st.markdown(f"**Estado:** {'🟢 Operando' if v.get('operando') else '🔴 Parada'}")
        if not v.get('operando'):
            st.markdown(f"**Motivo:** {limpia_texto(v.get('motivo', ''))}")
            mins = minutos_desde_hora(v.get('desde'))
            if mins is not None:
                st.markdown(f"**Tiempo parada:** {mins} min")

        # Datos del artículo
        if v.get('titulo'):
            st.markdown(f"**Artículo:** {v['titulo']}")
        if v.get('velocidad'):
            st.markdown(f"**Velocidad:** {v['velocidad']}")

        # Historial de paros del día
        st.divider()
        st.markdown("**Historial de paros de hoy**")
        df   = v.get('df_paro')
        cols = v.get('cols_paro')
        if df is not None and cols:
            hoy     = pd.Timestamp(datetime.now().date())
            df_hoy  = df[df[cols['dia']] == hoy].copy()
            df_hoy  = df_hoy[df_hoy[cols['codigo']].astype(str) != '0']  # excluir filas de producción
            if df_hoy.empty:
                st.caption("Sin paros registrados hoy. 🎉")
            else:
                tabla = df_hoy[[cols['turno'], cols['inicio'], cols['fin'],
                                cols['duracion'], cols['motivo']]].copy()
                tabla.columns = ['Turno', 'Inicio', 'Fin', 'Duración', 'Motivo']
                st.dataframe(tabla, use_container_width=True, hide_index=True)
        else:
            st.caption("No hay datos de historial disponibles.")

    # Mostrar como ventana emergente (dialog) si la versión de Streamlit lo soporta
    if hasattr(st, 'dialog'):
        st.dialog(f"Detalle · C-{num:02d}")(contenido)()
    else:
        with st.expander(f"Detalle · C-{num:02d}", expanded=True):
            contenido()


# =============================================================================
# TARJETAS DE MÁQUINAS (cuadrícula de 4 columnas)
# =============================================================================
def html_tarjeta_operando(num, v):
    """Genera el HTML de una tarjeta cuando la máquina está operando."""
    turno    = f"T: {turno_a_numero(v.get('turno', '—'))}"
    efic     = v.get('efic_turno')
    clase    = color_eficiencia(efic)
    vel      = v.get('velocidad')
    vel_txt  = f"{vel:.1f}" if vel and str(vel) not in ['nan', 'None'] else "—"
    hank     = v.get('hank')
    hank_txt = f"{hank:.3f}" if hank and str(hank) not in ['nan', 'None'] else "—"
    titulo   = v.get('titulo') or "—"

    return ''.join([
        f'<div class="card ok">',
        f'<div class="card-head">',
        f'<div style="display:flex;align-items:baseline;gap:10px;">',
        f'<div class="card-title">C-{num:02d}</div>',
        f'<div class="card-turno">{turno}</div>',
        f'</div>',
        f'<span class="badge ok">OPERANDO</span>',
        f'</div>',
        f'<div class="card-sub">Continua de Anillo</div>',
        f'<div style="display:flex;align-items:center;gap:14px;margin-top:8px;">',
        html_anillo(efic, clase),
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;">',
        f'<div class="metric"><div class="v">{vel_txt}</div><div class="l">VELOCIDAD</div></div>',
        f'<div class="metric"><div class="v">{hank_txt}</div><div class="l">HANK</div></div>',
        f'<div class="metric" style="grid-column:1/-1">',
        f'<div class="v" style="font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{titulo}</div>',
        f'<div class="l">ARTÍCULO</div></div>',
        f'</div></div>',
        f'</div>',
    ])


def html_tarjeta_parada(num, v):
    """Genera el HTML de una tarjeta cuando la máquina está parada."""
    turno    = f"T: {turno_a_numero(v.get('turno', '—'))}"
    motivo   = limpia_texto(v.get('motivo', ''))
    mins     = minutos_desde_hora(v.get('desde'))
    desde    = f"Desde hace {mins} min" if mins is not None else ""

    return ''.join([
        f'<div class="card bad">',
        f'<div class="card-head">',
        f'<div style="display:flex;align-items:baseline;gap:10px;">',
        f'<div class="card-title">C-{num:02d}</div>',
        f'<div class="card-turno">{turno}</div>',
        f'</div>',
        f'<span class="badge bad">PARADA</span>',
        f'</div>',
        f'<div class="card-sub">Continua de Anillo</div>',
        f'<div class="stop-reason">{motivo}</div>',
        f'<div class="stop-since">{desde}</div>',
        f'</div>',
    ])


# Dibujar la cuadrícula de tarjetas
N_COLUMNAS = 4
lista_maquinas = sorted(maquinas.items())
filas = [lista_maquinas[i:i+N_COLUMNAS] for i in range(0, len(lista_maquinas), N_COLUMNAS)]

for fila in filas:
    columnas = st.columns(N_COLUMNAS)
    for i, (num, v) in enumerate(fila):
        with columnas[i]:
            operando = v.get('operando', False)
            if operando:
                st.markdown(html_tarjeta_operando(num, v), unsafe_allow_html=True)
            else:
                st.markdown(html_tarjeta_parada(num, v), unsafe_allow_html=True)

            # Botón lupa (abre el detalle)
            if st.button("🔍", key=f"lupa_{num}"):
                mostrar_detalle(num, v)

# =============================================================================
# PIE DE PÁGINA
# =============================================================================
st.divider()
st.caption("Datos cargados desde archivos CSV del contador. Próximo paso: conexión directa a base de datos.")
