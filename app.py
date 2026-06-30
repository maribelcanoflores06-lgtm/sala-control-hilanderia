import streamlit as st
import pandas as pd
import re
import unicodedata
from datetime import datetime

st.set_page_config(page_title="Sala de Control · Hilandería", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# Estilos (mismo lenguaje visual del panel SCADA: fondo oscuro, acentos verde/ámbar/rojo)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root{
  --bg:#0B0F14; --panel:#121922; --panel2:#161E29; --line:#232E3B;
  --text:#E8EDF2; --text2:#7C8A99;
  --ok:#3DDC84; --ok-dim:#1E5E3E;
  --warn:#F5A623; --warn-dim:#5B4419;
  --bad:#E2424D; --bad-dim:#5A2025;
}
.stApp { background: var(--bg); color: var(--text); font-family:'Inter',sans-serif; }
[data-testid="stHeader"] { background: var(--bg); }
.block-container { padding-top: 1rem; max-width: 1500px; }

.topbar{
  display:flex; justify-content:space-between; align-items:center;
  background:var(--panel); border:1px solid var(--line); border-radius:10px;
  padding:14px 20px; margin-bottom:14px;
}
.topbar h1{
  font-family:'Rajdhani',sans-serif; font-weight:700; font-size:22px; margin:0;
  letter-spacing:1px; display:flex; align-items:center; gap:10px;
}
.dot{ width:10px; height:10px; border-radius:50%; background:var(--ok); display:inline-block; box-shadow:0 0 8px var(--ok);}
.kpi-row{ display:flex; gap:28px; align-items:center; }
.kpi{ text-align:center; }
.kpi .num{ font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:700; }
.kpi .lbl{ font-size:10px; color:var(--text2); letter-spacing:1px; }
.kpi.ok .num{ color:var(--ok); }
.kpi.bad .num{ color:var(--bad); }
.kpi.warn .num{ color:var(--warn); }

.alarm-bar{
  background:var(--bad-dim); border:1px solid var(--bad); border-radius:8px;
  padding:8px 16px; margin-bottom:16px; font-family:'JetBrains Mono',monospace;
  font-size:13px; color:#ffd9dc; overflow-x:auto; white-space:nowrap;
}

.card{
  background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--line);
  border-radius:10px; padding:14px 16px 36px 16px; margin-bottom:14px; min-height:150px;
  position:relative;
}
.card.ok{ border-left-color:var(--ok); }
.card.bad{ border-left-color:var(--bad); }
.card-head{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:2px;}
.card-title{ font-family:'Rajdhani',sans-serif; font-weight:700; font-size:18px; }
.card-turno{ font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--text2); font-weight:600; }
.card-sub{ font-size:11px; color:var(--text2); margin-top:-2px; margin-bottom:8px;}
.badge{ font-size:10px; font-weight:700; padding:3px 8px; border-radius:5px; letter-spacing:0.5px; }
.badge.ok{ background:var(--ok-dim); color:var(--ok); }
.badge.bad{ background:var(--bad-dim); color:var(--bad); }
.metrics{ display:flex; gap:18px; margin-top:8px; }
.metric .v{ font-family:'JetBrains Mono',monospace; font-weight:700; font-size:15px; }
.metric .l{ font-size:9px; color:var(--text2); letter-spacing:0.5px; }
.stop-reason{ color:var(--bad); font-size:12px; font-weight:600; margin-top:4px;}
.stop-since{ color:var(--text2); font-size:11px; }
.ring-wrap{ position:relative; width:62px; height:62px; flex-shrink:0; }
.ring-outer{ width:62px; height:62px; border-radius:50%; }
.ring-inner{
  position:absolute; top:7px; left:7px;
  width:48px; height:48px; border-radius:50%;
  background:var(--panel2);
  display:flex; align-items:center; justify-content:center;
  font-family:'JetBrains Mono',monospace; font-weight:700; font-size:16px;
}
.card-lupa{
  position:absolute; bottom:8px; right:10px;
  font-size:16px; color:var(--text2); opacity:0.5;
}
div[data-testid="stButton"]{
  margin-top:-34px;
  margin-bottom:14px;
  display:flex;
  justify-content:flex-end;
  padding-right:10px;
  position:relative;
  z-index:10;
}
div[data-testid="stButton"] > button{
  width:26px; height:26px; min-height:26px;
  border-radius:50%;
  background:rgba(30,42,56,0.95);
  border:1px solid #2D3E50;
  color:#5a8fa8;
  font-size:13px;
  padding:0;
  line-height:1;
  cursor:pointer;
}
div[data-testid="stButton"] > button:hover{
  background:rgba(79,163,209,0.25);
  border-color:#4FA3D1;
  color:#7FC4FF;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normaliza_col(c):
    c = str(c).strip().lower()
    c = unicodedata.normalize('NFKD', c).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', c)


def encuentra_col(df, candidatos):
    cols = list(df.columns)
    for cand in candidatos:
        if cand in cols:
            return cand
    for cand in candidatos:
        for c in cols:
            if cand in c:
                return c
    return None


def extrae_num_maquina(nombre_archivo, df=None, col_maquina=None):
    """Intenta sacar el número de máquina del nombre del archivo; si no, del propio CSV."""
    m = re.search(r'(?:_N_|N°|N_|n_|maquina[_ ]?)(\d+)', nombre_archivo, re.IGNORECASE)
    if m:
        return int(m.group(1))
    if df is not None and col_maquina is not None and not df.empty:
        try:
            return int(df[col_maquina].dropna().iloc[0])
        except Exception:
            pass
    return None


def ring_class(pct):
    """Devuelve la clase CSS del anillo según el porcentaje."""
    if pct is None:
        return "grey"
    if pct >= 85:
        return "ok"
    if pct >= 60:
        return "warn"
    return "bad"


def ring_color(eff):
    if eff is None:
        return "#7C8A99", "rgba(124,138,153,0.15)"
    if eff >= 85:
        return "#3DDC84", "rgba(61,220,132,0.15)"
    if eff >= 60:
        return "#F5A623", "rgba(245,166,35,0.15)"
    return "#E2424D", "rgba(226,66,77,0.15)"


def anillo_relleno(pct, color):
    """Genera un anillo tipo 'pastel' que se llena proporcionalmente al porcentaje."""
    pct = 0 if pct is None else max(0, min(100, pct))
    return f'background: conic-gradient({color} 0% {pct}%, rgba(255,255,255,0.10) {pct}% 100%); color:#fff; border:none;'


def turno_numero(letra):
    """Convierte A/B/C a 1/2/3 para mostrar al usuario."""
    mapa = {'A': '1', 'B': '2', 'C': '3'}
    letra_limpia = str(letra).strip().upper()[:1]
    return mapa.get(letra_limpia, letra)


def turno_actual():
    h = datetime.now().hour
    if 7 <= h < 15:
        return 'A'
    if 15 <= h < 23:
        return 'B'
    return 'C'


def turno_rango(turno):
    """Devuelve (hora_inicio, hora_fin) del turno A/B/C."""
    if turno == 'A':
        return 7, 15
    if turno == 'B':
        return 15, 23
    return 23, 7  # turno C cruza medianoche


def calcula_disponibilidad(df_m, col_dia, col_turno, col_inicio, col_fin, col_codigo, col_duracion):
    """Calcula % de tiempo trabajando del turno actual, usando el detalle de paros."""
    ahora = datetime.now()
    turno = turno_actual()
    hoy_real = pd.Timestamp(ahora.date())

    df_t = df_m[(df_m[col_dia] == hoy_real) & (df_m[col_turno].astype(str).str.upper().str.startswith(turno))]
    if df_t.empty:
        return None

    trabajado_min = 0.0
    for _, fila in df_t.iterrows():
        codigo = str(fila[col_codigo]).strip()
        fin_vacio = pd.isna(fila[col_fin]) or str(fila[col_fin]).strip() == ''
        if codigo == '0':
            if fin_vacio:
                # Tramo de producción aún abierto: cuenta desde su inicio hasta ahora
                mins = minutos_desde(fila[col_inicio])
                trabajado_min += mins if mins is not None else 0
            else:
                dur = duracion_a_minutos(fila[col_duracion])
                trabajado_min += dur if dur else 0

    h_ini, h_fin = turno_rango(turno)
    inicio_turno = ahora.replace(hour=h_ini, minute=0, second=0, microsecond=0)
    if turno == 'C' and ahora.hour < h_fin:
        # estamos después de medianoche, el turno C empezó "ayer" a las 23:00
        inicio_turno = inicio_turno - pd.Timedelta(days=1)
    transcurrido_min = (ahora - inicio_turno).total_seconds() / 60
    if transcurrido_min <= 0:
        return None

    disponibilidad = (trabajado_min / transcurrido_min) * 100
    return max(0, min(100, disponibilidad))


def duracion_a_minutos(val):
    try:
        h, m, s = str(val).split(':')
        return int(h) * 60 + int(m) + int(s) / 60
    except Exception:
        return None


def minutos_desde(hhmmss):
    try:
        h, m, s = [int(x) for x in str(hhmmss).split(':')]
        ahora = datetime.now()
        ref = ahora.replace(hour=h, minute=m, second=s, microsecond=0)
        diff = (ahora - ref).total_seconds() / 60
        if diff < 0:
            diff += 24 * 60
        return int(diff)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Carga de archivos (colapsada por defecto para no distraer del dashboard)
# ---------------------------------------------------------------------------
st.markdown("### 🧵 Sala de Control · Hilandería")

with st.expander("📂 Cargar / actualizar archivos CSV", expanded=not st.session_state.get('archivos_cargados', False)):
    col1, col2 = st.columns(2)
    with col1:
        files_prod = st.file_uploader(
            "Archivos de Producción / Eficiencia (uno o varios, Continua_N_X...)",
            type="csv", accept_multiple_files=True, key="prod"
        )
    with col2:
        files_paro = st.file_uploader(
            "Archivos de Paros (uno o varios, PARO_ORD_Continua_N_X...)",
            type="csv", accept_multiple_files=True, key="paro"
        )

if not files_prod or not files_paro:
    st.info("⬆️ Abre el panel '📂 Cargar / actualizar archivos CSV' de arriba para subir los datos.")
    st.stop()

# Marcar que ya hay archivos cargados (para colapsar el expander automáticamente)
st.session_state['archivos_cargados'] = True

# ---------------------------------------------------------------------------
# Procesar cada máquina
# ---------------------------------------------------------------------------
maquinas_data = {}

COLS_PROD = ['huso','maquina','dia','turno','hank','eficiencia','velocidad',
             'hr. producidas','hr. sin producir','codigo','titulo']

for f in files_prod:
    # Detectar si tiene encabezado: si la primera columna es texto ('huso') tiene header, si es número no tiene
    muestra = pd.read_csv(f, nrows=1, header=None)
    f.seek(0)
    tiene_header = str(muestra.iloc[0, 0]).strip().lower() == 'huso'
    df = pd.read_csv(f, header=0 if tiene_header else None)
    if not tiene_header:
        df.columns = COLS_PROD[:len(df.columns)]
    df.columns = [normaliza_col(c) for c in df.columns]
    col_maq = encuentra_col(df, ['maquina'])
    col_dia = encuentra_col(df, ['dia'])
    col_turno = encuentra_col(df, ['turno'])
    col_eff = encuentra_col(df, ['eficiencia'])
    col_vel = encuentra_col(df, ['velocidad'])
    col_titulo = encuentra_col(df, ['titulo'])
    col_hank = encuentra_col(df, ['hank'])
    if not all([col_maq, col_dia, col_turno, col_eff]):
        st.warning(f"⚠️ No pude leer bien el archivo de producción '{f.name}' (columnas no reconocidas).")
        continue
    df[col_dia] = pd.to_datetime(df[col_dia], format='%d/%m/%Y', errors='coerce')
    num_maq = extrae_num_maquina(f.name, df, col_maq)
    if num_maq is None:
        st.warning(f"⚠️ No pude identificar el número de máquina en '{f.name}'.")
        continue
    hoy = df[col_dia].max()
    df_hoy = df[df[col_dia] == hoy]
    # Preferir la fila del turno actual real (ej. si son las 11am, turno A);
    # si no existe, usar la última fila disponible del día.
    turno_hoy = turno_actual()
    df_turno = df_hoy[df_hoy[col_turno].astype(str).str.upper().str.startswith(turno_hoy)]
    if not df_turno.empty:
        ultima = df_turno.iloc[-1]
    elif not df_hoy.empty:
        ultima = df_hoy.iloc[-1]
    else:
        ultima = df.iloc[-1]
    maquinas_data.setdefault(num_maq, {})['eficiencia'] = float(ultima[col_eff])
    maquinas_data[num_maq]['turno'] = ultima[col_turno]
    if col_vel:
        maquinas_data[num_maq]['velocidad'] = ultima[col_vel]
    if col_titulo:
        maquinas_data[num_maq]['titulo'] = ultima[col_titulo]
    if col_hank:
        maquinas_data[num_maq]['hank'] = ultima[col_hank]

for f in files_paro:
    df = pd.read_csv(f)
    df.columns = [normaliza_col(c) for c in df.columns]
    col_maq = encuentra_col(df, ['num. maquina', 'num maquina', 'maquina'])
    col_dia_p = encuentra_col(df, ['dia'])
    col_turno_p = encuentra_col(df, ['turno'])
    col_inicio = encuentra_col(df, ['inicio'])
    col_fin = encuentra_col(df, ['fin'])
    col_codigo = encuentra_col(df, ['codigo de paro', 'codigo'])
    col_motivo = encuentra_col(df, ['motivo de paro', 'motivo'])
    col_duracion = encuentra_col(df, ['duracion'])
    if not all([col_maq, col_dia_p, col_turno_p, col_inicio, col_fin, col_codigo, col_motivo, col_duracion]):
        st.warning(f"⚠️ No pude leer bien el archivo de paros '{f.name}' (columnas no reconocidas).")
        continue
    df[col_dia_p] = pd.to_datetime(df[col_dia_p], format='%d/%m/%Y', errors='coerce')
    num_maq = extrae_num_maquina(f.name, df, col_maq)
    if num_maq is None:
        st.warning(f"⚠️ No pude identificar el número de máquina en '{f.name}'.")
        continue
    ultima = df.iloc[-1]
    abierta = pd.isna(ultima[col_fin]) or str(ultima[col_fin]).strip() == ''
    codigo = str(ultima[col_codigo]).strip()
    operando = abierta and codigo == '0'
    maquinas_data.setdefault(num_maq, {})
    maquinas_data[num_maq]['operando'] = operando
    maquinas_data[num_maq]['motivo'] = ultima[col_motivo] if not operando else None
    maquinas_data[num_maq]['desde'] = ultima[col_inicio]
    maquinas_data[num_maq]['abierta'] = abierta
    maquinas_data[num_maq]['disponibilidad'] = calcula_disponibilidad(
        df, col_dia_p, col_turno_p, col_inicio, col_fin, col_codigo, col_duracion
    )
    maquinas_data[num_maq]['df_paro'] = df
    maquinas_data[num_maq]['cols_paro'] = {
        'dia': col_dia_p, 'turno': col_turno_p, 'inicio': col_inicio,
        'fin': col_fin, 'codigo': col_codigo, 'motivo': col_motivo, 'duracion': col_duracion,
    }

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
total = len(maquinas_data)
operando_n = sum(1 for v in maquinas_data.values() if v.get('operando'))
paradas_n = total - operando_n
disponibilidades = [v['disponibilidad'] for v in maquinas_data.values() if v.get('disponibilidad') is not None]
eff_prom = sum(disponibilidades) / len(disponibilidades) if disponibilidades else 0
hora_local = datetime.now().strftime("%H:%M:%S")

topbar_html = (
    '<div class="topbar">'
    '<h1><span class="dot"></span>FLOTA DE MÁQUINAS</h1>'
    '<div class="kpi-row">'
    f'<div class="kpi ok"><div class="num">{operando_n}/{total}</div><div class="lbl">OPERANDO</div></div>'
    f'<div class="kpi bad"><div class="num">{paradas_n}</div><div class="lbl">PARADAS</div></div>'
    f'<div class="kpi warn"><div class="num">{eff_prom:.1f}%</div><div class="lbl">EFICIENCIA PROM.</div></div>'
    f'<div class="kpi"><div class="num">{hora_local}</div><div class="lbl">HORA LOCAL</div></div>'
    '</div></div>'
)
st.markdown(topbar_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Ticker de alarmas
# ---------------------------------------------------------------------------
alarmas = []
for maq, v in sorted(maquinas_data.items()):
    motivo = v.get('motivo', '')
    if not v.get('operando') and motivo and str(motivo).strip().lower() not in ['nan','none','']:
        mins = minutos_desde(v.get('desde'))
        txt = f"C-{maq:02d} — {motivo}"
        if mins is not None:
            txt += f" · hace {mins} min"
        alarmas.append(txt)

if alarmas:
    alarm_html = '<div class="alarm-bar">⚠️ ALARMAS&nbsp;&nbsp;&nbsp;' + '&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;'.join(alarmas) + '</div>'
    st.markdown(alarm_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tarjetas por máquina
# ---------------------------------------------------------------------------
def muestra_detalle(maq, v):
    """Abre una ventana con el historial de la máquina."""
    def _contenido():
        operando = v.get('operando')
        disp = v.get('disponibilidad')
        rc = ring_class(disp)

        # Anillo de disponibilidad siempre visible en el detalle
        if disp is not None:
            st.markdown(ring_html(disp, rc), unsafe_allow_html=True)
            st.markdown(f"**Eficiencia del turno: {disp:.1f}%**")
        
        st.markdown(f"**Estado:** {'🟢 Operando' if operando else '🔴 Parada'}")

        if not operando:
            motivo = v.get('motivo', '')
            if not motivo or str(motivo).strip().lower() in ['nan','none','']:
                motivo = "Registrando motivo..."
            st.markdown(f"**Motivo:** {motivo}")
            mins = minutos_desde(v.get('desde'))
            if mins is not None:
                st.markdown(f"**Tiempo parada:** {mins} min")

        if v.get('titulo'):
            st.markdown(f"**Artículo:** {v['titulo']}")
        if v.get('velocidad'):
            st.markdown(f"**Velocidad:** {v['velocidad']}")

        st.divider()
        st.markdown("**Historial de paros de hoy**")

        df = v.get('df_paro')
        cols = v.get('cols_paro')
        if df is not None and cols:
            hoy_real = pd.Timestamp(datetime.now().date())
            df_hoy = df[df[cols['dia']] == hoy_real].copy()
            df_hoy = df_hoy[df_hoy[cols['codigo']].astype(str) != '0']  # solo paros reales, no producción
            if df_hoy.empty:
                st.caption("Sin paros registrados hoy. 🎉")
            else:
                tabla = df_hoy[[cols['turno'], cols['inicio'], cols['fin'], cols['duracion'], cols['motivo']]].copy()
                tabla.columns = ['Turno', 'Inicio', 'Fin', 'Duración', 'Motivo']
                st.dataframe(tabla, use_container_width=True, hide_index=True)
        else:
            st.caption("No hay datos de historial disponibles.")

    if hasattr(st, 'dialog'):
        st.dialog(f"Detalle · Máquina C-{maq:02d}")(_contenido)()
    else:
        with st.expander(f"Detalle · Máquina C-{maq:02d}", expanded=True):
            _contenido()


def ring_html(pct, rc):
    """Anillo progresivo: conic-gradient como fondo + círculo interior encima."""
    pct_val = 0 if pct is None else max(0, min(100, pct))
    colores = {'ok': '#3DDC84', 'warn': '#F5A623', 'bad': '#E2424D', 'grey': '#7C8A99'}
    color = colores.get(rc, '#7C8A99')
    txt = f"{int(pct_val)}" if pct is not None else "—"
    grad = f"conic-gradient({color} 0% {pct_val}%, #1e2a38 {pct_val}% 100%)"
    return (
        f'<div class="ring-wrap">'
        f'<div class="ring-outer" style="background:{grad};"></div>'
        f'<div class="ring-inner" style="color:{color};">{txt}</div>'
        f'</div>'
    )


n_cols = 4
maquinas_ordenadas = sorted(maquinas_data.items())
rows = [maquinas_ordenadas[i:i+n_cols] for i in range(0, len(maquinas_ordenadas), n_cols)]

for row in rows:
    cols = st.columns(n_cols)
    for i, (maq, v) in enumerate(row):
        operando = v.get('operando', False)
        estado_clase = "ok" if operando else "bad"
        badge_txt = "OPERANDO" if operando else "PARADA"
        turno_txt = f"T: {turno_numero(v.get('turno', '—'))}"

        with cols[i]:
            partes = [
                f'<div class="card {estado_clase}">',
                # Header: C-05 | T:1 | badge
                '<div class="card-head">',
                '<div style="display:flex;align-items:baseline;gap:10px;">',
                f'<div class="card-title">C-{maq:02d}</div>',
                f'<div class="card-turno">{turno_txt}</div>',
                '</div>',
                f'<span class="badge {estado_clase}">{badge_txt}</span>',
                '</div>',
                '<div class="card-sub">Continua de Anillo</div>',
            ]

            if operando:
                disp = v.get('disponibilidad')
                rc = ring_class(disp)
                titulo = v.get('titulo', '—')
                vel = v.get('velocidad')
                vel_txt = f"{vel:.1f}" if vel is not None and str(vel) not in ['—', 'nan'] else "—"
                hank = v.get('hank')
                hank_txt = f"{hank:.3f}" if hank is not None and str(hank) not in ['—', 'nan'] else "—"
                partes += [
                    '<div style="display:flex;align-items:center;gap:14px;margin-top:8px;">',
                    ring_html(disp, rc),
                    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;">',
                    f'<div class="metric"><div class="v">{vel_txt}</div><div class="l">VELOCIDAD</div></div>',
                    f'<div class="metric"><div class="v">{hank_txt}</div><div class="l">HANK</div></div>',
                    f'<div class="metric" style="grid-column:1/-1"><div class="v" style="font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{titulo}</div><div class="l">ARTÍCULO</div></div>',
                    '</div>',
                    '</div>',
                ]
            else:
                mins = minutos_desde(v.get('desde'))
                desde_txt = f"Desde hace {mins} min" if mins is not None else ""
                motivo = v.get('motivo', '')
                # Limpiar valores inválidos
                if not motivo or str(motivo).strip().lower() in ['nan', 'none', 'motivo no disponible', '']:
                    motivo = "Registrando motivo..."
                if not desde_txt or str(v.get('desde','')).strip().lower() in ['nan','none','']:
                    desde_txt = ""
                partes += [
                    f'<div class="stop-reason">{motivo}</div>',
                    f'<div class="stop-since">{desde_txt}</div>',
                ]

            partes.append('</div>')
            st.markdown(''.join(partes), unsafe_allow_html=True)
            if st.button("🔍", key=f"detalle_{maq}"):
                muestra_detalle(maq, v)

st.divider()
st.caption("Datos cargados manualmente desde los archivos descargados por VNC. Próximo paso: automatizar la carga sin subir archivos a mano.")
