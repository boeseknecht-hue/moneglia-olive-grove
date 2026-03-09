"""
Olive Grove Management App — Moneglia, Italy  v2.0
===================================================
Digital Twin | Visura Catastale Data | Weather Integration
----------------------------------------------------------
Setup:
    pip install -r requirements.txt

Run locally:
    streamlit run olive_grove_app.py

Deploy:
    Push to GitHub → connect to share.streamlit.io
    Add secret: OWM_API_KEY = "<your OpenWeatherMap key>"
"""

import os
import datetime
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Olive Grove Manager | Moneglia",
    page_icon="🫒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal custom CSS for desktop polish ─────────────────────────────────────
st.markdown(
    """
    <style>
        /* Wider sidebar */
        [data-testid="stSidebar"] { min-width: 270px; max-width: 270px; }
        /* Metric card styling */
        [data-testid="metric-container"] {
            background: #f7f9f4;
            border: 1px solid #d4e6c3;
            border-radius: 10px;
            padding: 12px 16px;
        }
        /* Alert box fonts */
        .alert-box {
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            font-size: 1rem;
            font-weight: 500;
        }
        .frost-alert  { background:#fff3cd; border-left:5px solid #f0a500; color:#7a4f00; }
        .harvest-open { background:#d4edda; border-left:5px solid #28a745; color:#155724; }
        .harvest-wait { background:#f8d7da; border-left:5px solid #dc3545; color:#721c24; }
        /* Pest risk levels */
        .risk-low    { background:#d4edda; border-left:6px solid #28a745; color:#155724; }
        .risk-medium { background:#fff3cd; border-left:6px solid #f0a500; color:#7a4f00; }
        .risk-high   { background:#f8d7da; border-left:6px solid #dc3545; color:#721c24; }
        /* Risk status bar */
        .risk-bar-wrap {
            background:#e9ecef; border-radius:20px; height:26px;
            width:100%; position:relative; overflow:hidden; margin:8px 0 18px 0;
        }
        .risk-bar-fill {
            height:100%; border-radius:20px;
            display:flex; align-items:center; padding-left:14px;
            font-weight:700; font-size:0.85rem; letter-spacing:0.04em;
            transition: width 0.4s ease;
        }
        /* Table header */
        thead tr th { background:#4a7c59 !important; color:white !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS — Official Visura Catastale data
# ══════════════════════════════════════════════════════════════════════════════
MONEGLIA_LAT  = 44.2445   # Località Crovetta
MONEGLIA_LON  = 9.4880    # Località Crovetta
FOGLIO        = "13"
TOTAL_HA      = 1.3450
TOTAL_M2      = 13_450
TREE_BASELINE = 310          # 230 trees/ha × 1.345 ha
DENSITY_PER_HA = 230

# Agricultural plots (Catasto Terreni)
PLOTS = [
    {"mappale": "2671", "area_m2": 1_266, "qualita": "Uliveto",       "classe": "1"},
    {"mappale": "2675", "area_m2": 3_608, "qualita": "Sem Irr Arb",   "classe": "—"},
    {"mappale": "2677", "area_m2": 5_302, "qualita": "Uliveto",       "classe": "1"},
    {"mappale": "2679", "area_m2": 3_274, "qualita": "Uliveto",       "classe": "1"},
]

# Structural assets (Catasto Fabbricati — same Foglio)
STRUCTURES = [
    {"mappale": "2670", "tipo": "Main Residence",  "tipo_it": "Residenza principale", "vani": 8,   "mq": None},
    {"mappale": "2673", "tipo": "Storage Unit A",  "tipo_it": "Deposito A",           "vani": None, "mq": 58},
    {"mappale": "2674", "tipo": "Storage Unit B",  "tipo_it": "Deposito B",           "vani": None, "mq": 58},
]

HARVEST_START_MONTH = 10  # October
HARVEST_START_DAY   = 15
FROST_THRESHOLD_C   = 2.0

# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATIONS
# ══════════════════════════════════════════════════════════════════════════════
LANG = {
    "en": {
        # General
        "app_title":    "🫒 Olive Grove Manager",
        "app_subtitle": "Moneglia, Liguria — Italy  ·  Digital Twin v2.0",
        "nav_label":    "Navigation",
        "nav_overview": "Grove Overview",
        "nav_weather":  "Weather & Alerts",
        "nav_map":      "Interactive Map",
        "nav_tasks":    "Seasonal Tasks",
        "footer":       "Olive Grove Manager v2.0 · Built with Streamlit · Data: Visura Catastale",

        # Overview
        "overview_header": "Grove Overview — Official Visura Data",
        "overview_intro": (
            "Your olive grove is officially registered in **Foglio n. 13** of the "
            "Catasto Terreni, Comune di Moneglia (GE). All figures below are sourced "
            "directly from the Visura Catastale."
        ),
        "m_total_area":   "Total Surface Area",
        "m_total_area_v": f"{TOTAL_M2:,} m²  (1.3450 ha)",
        "m_plots":        "Agricultural Plots",
        "m_plots_v":      "4 cadastral parcels",
        "m_trees":        "Tree Baseline",
        "m_trees_v":      f"310 olive trees",
        "m_foglio":       "Foglio",
        "m_foglio_v":     "n. 13 — Moneglia (GE)",
        "plots_header":   "📋 Cadastral Parcels (Terreni) — Foglio 13",
        "col_mappale":    "Mappale",
        "col_qualita":    "Qualità",
        "col_classe":     "Classe",
        "col_area_m2":    "Area (m²)",
        "col_area_ha":    "Area (ha)",
        "col_trees":      "Est. Trees",
        "struct_header":  "🏠 Structures (Fabbricati) — Foglio 13",
        "col_type":       "Type",
        "col_rooms":      "Rooms / Size",
        "struct_note":    (
            "Main residence (8 rooms) and two storage units (total 116 m²) located "
            "on adjacent mappali 2670, 2673, 2674."
        ),

        # Weather
        "wx_header":      "Weather & Agricultural Alerts",
        "wx_api_label":   "OpenWeatherMap API Key",
        "wx_api_hint":    "Enter your free API key from openweathermap.org",
        "wx_fetch":       "Fetch 7-Day Forecast",
        "wx_fetching":    "Fetching forecast from OpenWeatherMap…",
        "wx_error":       "⚠️ Could not retrieve weather data. Check your API key.",
        "wx_7day":        "7-Day Forecast — Moneglia",
        "wx_col_date":    "Date",
        "wx_col_desc":    "Conditions",
        "wx_col_max":     "Max °C",
        "wx_col_min":     "Min °C",
        "wx_col_rain":    "Rain (mm)",
        "wx_col_wind":    "Wind (km/h)",
        "alert_header":   "🚨 Agricultural Alerts",
        "frost_alert":    "❄️  Frost Risk — Delay Pruning",
        "frost_detail":   "Min temperature drops below 2 °C within the next 7 days. Postpone any pruning work until conditions improve.",
        "harvest_open":   "🍂  Harvest Window Open",
        "harvest_wait":   "🍂  Harvest Window: Monitoring",
        "harvest_rain":   "⚠️  High rainfall detected — harvest window may be affected.",
        "harvest_logic":  "Harvest window opens Oct 15. Status is adjusted for current rainfall trends.",
        "wx_demo":        "ℹ️  Demo mode — enter an API key above to load live data.",

        # Biological Risk Monitor
        "bio_nav":        "Biological Risk Monitor",
        "bio_header":     "Biological Risk Monitor — Bactrocera oleae (Olive Fruit Fly)",
        "bio_intro":      (
            "Real-time pest pressure assessment for **Bactrocera oleae** (Olive Fruit Fly) "
            "based on live temperature and humidity data from the Moneglia weather station. "
            "Risk thresholds follow standard agronomic guidelines for Ligurian olive groves."
        ),
        "bio_risk_label": "Current 7-Day Risk Level",
        "bio_low":        "🟢  LOW RISK",
        "bio_medium":     "🟡  MEDIUM RISK",
        "bio_high":       "🔴  HIGH RISK — Peak Activity",
        "bio_low_why":    "Average temperature is outside the fly's optimal range (15–32 °C). Population activity is suppressed.",
        "bio_medium_why": "Temperatures are in the marginal zone (15–20 °C). Monitor traps weekly.",
        "bio_high_why":   "Temperature (20–30 °C) and humidity (>50 %) are ideal for fly activity and egg-laying. Immediate action recommended.",
        "bio_advice_high": (
            "Conditions ideal for fly strike. Monitor traps and consider organic preventive treatments."
        ),
        "bio_thresholds": "Risk Thresholds — Bactrocera oleae",
        "bio_th_low":     "< 15 °C or > 32 °C avg",
        "bio_th_med":     "15 °C – 20 °C avg",
        "bio_th_high":    "20 °C – 30 °C avg + Humidity > 50 %",
        "bio_th_low_l":   "Low — Fly suppressed",
        "bio_th_med_l":   "Medium — Monitor traps",
        "bio_th_high_l":  "High — Peak Activity",
        "bio_wx_needed":  "⚠️  Connect an OpenWeatherMap API key on the **Weather & Alerts** page to enable live risk assessment.",
        "bio_wx_demo":    "Showing demo risk profile — connect API key for live data.",
        "bio_cost_header": "Protection Cost Estimator",
        "bio_cost_intro":  (
            "Based on **310 trees** across **1.3450 ha** (3 L solution per tree per full coverage):"
        ),
        "bio_cost_total_l": "Total solution per coverage",
        "bio_cost_copper_l": "Organic copper (Bordeaux mix)",
        "bio_cost_kaolin_l": "Kaolin clay (3 % suspension)",
        "bio_cost_coverages": "Estimated coverages per season",
        "bio_cost_note":   (
            "Dosage guidelines: Bordeaux mixture at 1 % concentration (1 kg copper sulfate + 1 kg lime per 100 L). "
            "Kaolin clay at 3 % (3 kg per 100 L). Consult your local agronomist for precise application rates."
        ),

        # Map
        "map_header":     "Interactive Map",
        "map_caption":    "Map centred on Località Crovetta, Moneglia (Lat 44.2445, Lon 9.4880). Zoom in to explore your grove.",
        "map_grove":      "🫒 Olive Grove — Foglio 13",
        "map_popup":      (
            "<b>🫒 Olive Grove</b><br>"
            "Foglio n. 13<br>"
            "Mappali: 2671, 2675, 2677, 2679<br>"
            "Total area: 13,450 m² (1.3450 ha)<br>"
            "Trees: ~310"
        ),
        "map_residence":  "🏠 Main Residence (Mappale 2670)",
        "map_storage":    "🏚 Storage (Mappali 2673, 2674)",

        # Tasks
        "tasks_header":   "Seasonal Task Calendar",
        "tasks_note":     "Track your seasonal olive grove activities. Checkboxes persist during your session.",
    },
    "it": {
        # General
        "app_title":    "🫒 Gestione Uliveto",
        "app_subtitle": "Moneglia, Liguria — Italia  ·  Gemello Digitale v2.0",
        "nav_label":    "Navigazione",
        "nav_overview": "Panoramica uliveto",
        "nav_weather":  "Meteo & Allerte",
        "nav_map":      "Mappa interattiva",
        "nav_tasks":    "Attività stagionali",
        "footer":       "Gestione Uliveto v2.0 · Creato con Streamlit · Dati: Visura Catastale",

        # Overview
        "overview_header": "Panoramica uliveto — Dati Visura Catastale",
        "overview_intro": (
            "Il tuo uliveto è ufficialmente registrato al **Foglio n. 13** del "
            "Catasto Terreni, Comune di Moneglia (GE). Tutti i dati provengono "
            "dalla Visura Catastale."
        ),
        "m_total_area":   "Superficie totale",
        "m_total_area_v": f"{TOTAL_M2:,} m²  (1,3450 ha)",
        "m_plots":        "Particelle agricole",
        "m_plots_v":      "4 particelle catastali",
        "m_trees":        "Olivi stimati",
        "m_trees_v":      f"310 piante di ulivo",
        "m_foglio":       "Foglio",
        "m_foglio_v":     "n. 13 — Moneglia (GE)",
        "plots_header":   "📋 Particelle (Terreni) — Foglio 13",
        "col_mappale":    "Mappale",
        "col_qualita":    "Qualità",
        "col_classe":     "Classe",
        "col_area_m2":    "Superficie (m²)",
        "col_area_ha":    "Superficie (ha)",
        "col_trees":      "Olivi stimati",
        "struct_header":  "🏠 Fabbricati — Foglio 13",
        "col_type":       "Tipo",
        "col_rooms":      "Vani / Superficie",
        "struct_note":    (
            "Residenza principale (8 vani) e due depositi (tot. 116 m²) situati "
            "sui mappali adiacenti 2670, 2673, 2674."
        ),

        # Weather
        "wx_header":      "Meteo & Allerte Agricole",
        "wx_api_label":   "Chiave API OpenWeatherMap",
        "wx_api_hint":    "Inserisci la tua chiave gratuita da openweathermap.org",
        "wx_fetch":       "Carica previsioni 7 giorni",
        "wx_fetching":    "Caricamento previsioni da OpenWeatherMap…",
        "wx_error":       "⚠️ Impossibile ottenere dati meteo. Verifica la chiave API.",
        "wx_7day":        "Previsioni 7 giorni — Moneglia",
        "wx_col_date":    "Data",
        "wx_col_desc":    "Condizioni",
        "wx_col_max":     "Max °C",
        "wx_col_min":     "Min °C",
        "wx_col_rain":    "Pioggia (mm)",
        "wx_col_wind":    "Vento (km/h)",
        "alert_header":   "🚨 Allerte agricole",
        "frost_alert":    "❄️  Rischio Gelata — Ritardare la potatura",
        "frost_detail":   "La temperatura minima scende sotto i 2 °C nei prossimi 7 giorni. Posticipare la potatura fino al miglioramento delle condizioni.",
        "harvest_open":   "🍂  Finestra di raccolta aperta",
        "harvest_wait":   "🍂  Finestra di raccolta: in monitoraggio",
        "harvest_rain":   "⚠️  Piogge elevate rilevate — la raccolta potrebbe essere influenzata.",
        "harvest_logic":  "La finestra di raccolta si apre il 15 ottobre. Lo stato è aggiornato in base alle tendenze di pioggia.",
        "wx_demo":        "ℹ️  Modalità demo — inserisci una chiave API per i dati in tempo reale.",

        # Biological Risk Monitor
        "bio_nav":        "Monitoraggio Rischio Biologico",
        "bio_header":     "Monitoraggio Rischio Biologico — Bactrocera oleae (Mosca dell'Olivo)",
        "bio_intro":      (
            "Valutazione in tempo reale della pressione da **Bactrocera oleae** (Mosca dell'Olivo) "
            "basata sui dati meteo live di Moneglia. "
            "Le soglie seguono le linee guida agronomiche per gli uliveti liguri."
        ),
        "bio_risk_label": "Livello di rischio attuale (7 giorni)",
        "bio_low":        "🟢  RISCHIO BASSO",
        "bio_medium":     "🟡  RISCHIO MEDIO",
        "bio_high":       "🔴  RISCHIO ALTO — Attività di picco",
        "bio_low_why":    "La temperatura media è al di fuori dell'intervallo ottimale per la mosca (15–32 °C). L'attività della popolazione è soppressa.",
        "bio_medium_why": "Le temperature sono nella zona marginale (15–20 °C). Monitorare le trappole settimanalmente.",
        "bio_high_why":   "Temperatura (20–30 °C) e umidità (>50 %) sono ideali per l'attività della mosca e la deposizione delle uova. Azione immediata consigliata.",
        "bio_advice_high": (
            "Condizioni ideali per la mosca. Monitorare le trappole e valutare trattamenti preventivi."
        ),
        "bio_thresholds": "Soglie di rischio — Bactrocera oleae",
        "bio_th_low":     "< 15 °C o > 32 °C media",
        "bio_th_med":     "15 °C – 20 °C media",
        "bio_th_high":    "20 °C – 30 °C media + Umidità > 50 %",
        "bio_th_low_l":   "Basso — Mosca soppressa",
        "bio_th_med_l":   "Medio — Monitorare le trappole",
        "bio_th_high_l":  "Alto — Attività di picco",
        "bio_wx_needed":  "⚠️  Inserisci una chiave API OpenWeatherMap nella pagina **Meteo & Allerte** per abilitare la valutazione live.",
        "bio_wx_demo":    "Profilo di rischio demo — inserisci chiave API per dati in tempo reale.",
        "bio_cost_header": "Stima Costi di Protezione",
        "bio_cost_intro":  (
            "Basato su **310 alberi** su **1,3450 ha** (3 L di soluzione per albero per copertura completa):"
        ),
        "bio_cost_total_l": "Soluzione totale per copertura",
        "bio_cost_copper_l": "Rame organico (poltiglia bordolese)",
        "bio_cost_kaolin_l": "Caolino (sospensione al 3 %)",
        "bio_cost_coverages": "Coperture stimate per stagione",
        "bio_cost_note":   (
            "Dosaggi indicativi: poltiglia bordolese all'1 % (1 kg solfato di rame + 1 kg calce per 100 L). "
            "Caolino al 3 % (3 kg per 100 L). Consultare il proprio agronomo per le dosi precise."
        ),

        # Map
        "map_header":     "Mappa interattiva",
        "map_caption":    "Mappa centrata su Località Crovetta, Moneglia (Lat 44.2445, Lon 9.4880). Usa lo zoom per esplorare l'uliveto.",
        "map_grove":      "🫒 Uliveto — Foglio 13",
        "map_popup":      (
            "<b>🫒 Uliveto</b><br>"
            "Foglio n. 13<br>"
            "Mappali: 2671, 2675, 2677, 2679<br>"
            "Superficie: 13.450 m² (1,3450 ha)<br>"
            "Olivi: ~310"
        ),
        "map_residence":  "🏠 Residenza principale (Mappale 2670)",
        "map_storage":    "🏚 Depositi (Mappali 2673, 2674)",

        # Tasks
        "tasks_header":   "Calendario attività stagionali",
        "tasks_note":     "Tieni traccia delle attività stagionali del tuo uliveto.",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# WEATHER HELPER
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_forecast(api_key: str) -> dict | None:
    """Call OWM 5-day/3-hour forecast, aggregate to daily, return dict or None."""
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={MONEGLIA_LAT}&lon={MONEGLIA_LON}"
        f"&appid={api_key}&units=metric&cnt=56"
    )
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        raw = r.json()
    except Exception:
        return None

    # Aggregate 3-hour slots → daily
    days: dict = {}
    humidity_acc: dict = {}   # accumulate humidity readings to average later
    for slot in raw.get("list", []):
        dt       = datetime.datetime.fromtimestamp(slot["dt"])
        day      = dt.date()
        temp     = slot["main"]
        humidity = slot["main"].get("humidity", 50)
        rain     = slot.get("rain", {}).get("3h", 0.0)
        wind     = slot["wind"]["speed"] * 3.6  # m/s → km/h
        desc     = slot["weather"][0]["description"].capitalize()
        if day not in days:
            days[day] = {"max": temp["temp_max"], "min": temp["temp_min"],
                         "rain": 0.0, "wind": wind, "desc": desc,
                         "humidity": humidity}
            humidity_acc[day] = [humidity]
        else:
            days[day]["max"]  = max(days[day]["max"], temp["temp_max"])
            days[day]["min"]  = min(days[day]["min"], temp["temp_min"])
            days[day]["rain"] += rain
            days[day]["wind"]  = max(days[day]["wind"], wind)
            humidity_acc[day].append(humidity)

    # Replace instantaneous humidity with daily average
    for day in days:
        days[day]["humidity"] = round(sum(humidity_acc[day]) / len(humidity_acc[day]))

    return dict(list(days.items())[:7])


def harvest_window_open() -> bool:
    today = datetime.date.today()
    open_date = datetime.date(today.year, HARVEST_START_MONTH, HARVEST_START_DAY)
    return today >= open_date


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/"
        "Flag_of_Liguria.svg/200px-Flag_of_Liguria.svg.png",
        width=80,
    )
    st.markdown("### 🫒 Olive Grove Manager")
    st.caption("Moneglia (GE) · Foglio 13")
    st.divider()

    lang_choice = st.radio(
        "🌐 Language / Lingua",
        options=["English 🇬🇧", "Italiano 🇮🇹"],
        index=0,
        key="lang_radio",
    )
    lang = "it" if "Italiano" in lang_choice else "en"
    T = LANG[lang]

    st.divider()
    page = st.radio(T["nav_label"], options=[
        T["nav_overview"],
        T["nav_weather"],
        T["bio_nav"],
        T["nav_map"],
        T["nav_tasks"],
    ], key="nav_radio")

    st.divider()
    st.caption(f"📍 Moneglia (GE), Liguria")
    st.caption(f"🗺️  Foglio 13 · 4 mappali · 1.3450 ha")
    st.caption(f"🫒 ~310 olive trees")
    st.caption(f"🏠 Residence + 116 m² storage")

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.title(T["app_title"])
st.markdown(f"*{T['app_subtitle']}*")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: GROVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == T["nav_overview"]:

    st.header(f"🌿 {T['overview_header']}")
    st.markdown(T["overview_intro"])
    st.write("")

    # ── Summary metrics ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T["m_total_area"], T["m_total_area_v"])
    c2.metric(T["m_plots"],      T["m_plots_v"])
    c3.metric(T["m_trees"],      T["m_trees_v"])
    c4.metric(T["m_foglio"],     T["m_foglio_v"])

    st.write("")

    # ── Agricultural plots ────────────────────────────────────────────────────
    st.subheader(T["plots_header"])

    rows = []
    for p in PLOTS:
        ha     = p["area_m2"] / 10_000
        trees  = round(ha * DENSITY_PER_HA) if p["qualita"] != "Sem Irr Arb" else "—"
        rows.append({
            T["col_mappale"]:  p["mappale"],
            T["col_qualita"]:  p["qualita"],
            T["col_classe"]:   p["classe"],
            T["col_area_m2"]:  f"{p['area_m2']:,}",
            T["col_area_ha"]:  f"{ha:.4f}",
            T["col_trees"]:    trees,
        })

    # Totals row
    total_trees_calc = sum(
        round((p["area_m2"] / 10_000) * DENSITY_PER_HA)
        for p in PLOTS if p["qualita"] != "Sem Irr Arb"
    )
    rows.append({
        T["col_mappale"]: "TOTAL",
        T["col_qualita"]: "—",
        T["col_classe"]:  "—",
        T["col_area_m2"]: f"{TOTAL_M2:,}",
        T["col_area_ha"]: f"{TOTAL_HA:.4f}",
        T["col_trees"]:   TREE_BASELINE,
    })

    st.table(rows)

    st.info(
        f"Tree baseline set to **{TREE_BASELINE} olive trees** "
        f"(density: {DENSITY_PER_HA} trees/ha × 1.3450 ha). "
        f"Mappale 2675 (Sem Irr Arb) is arable/mixed land — no olive tree count assigned."
        if lang == "en" else
        f"Baseline fissato a **{TREE_BASELINE} ulivi** "
        f"(densità: {DENSITY_PER_HA} piante/ha × 1,3450 ha). "
        f"Il mappale 2675 (Sem Irr Arb) è terreno seminativo/misto — nessun olivo assegnato."
    )

    st.write("")

    # ── Structures ────────────────────────────────────────────────────────────
    st.subheader(T["struct_header"])
    st.caption(T["struct_note"])

    struct_rows = []
    for s in STRUCTURES:
        tipo  = s["tipo_it"] if lang == "it" else s["tipo"]
        rooms = f"{s['vani']} vani" if s["vani"] else f"{s['mq']} m²"
        struct_rows.append({
            T["col_mappale"]: s["mappale"],
            T["col_type"]:    tipo,
            T["col_rooms"]:   rooms,
        })
    st.table(struct_rows)

    st.success(
        "🏠 Total built structures: 1 residence (8 rooms) + 116 m² storage across 3 mappali (2670, 2673, 2674)."
        if lang == "en" else
        "🏠 Strutture totali: 1 residenza (8 vani) + 116 m² di depositi su 3 mappali (2670, 2673, 2674)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WEATHER & ALERTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == T["nav_weather"]:

    st.header(f"🌤️ {T['wx_header']}")

    # API key input — first try Streamlit secrets, then let user type
    api_key = ""
    try:
        api_key = st.secrets["OWM_API_KEY"]
    except Exception:
        pass

    if not api_key:
        api_key = st.text_input(
            T["wx_api_label"],
            placeholder=T["wx_api_hint"],
            type="password",
            key="owm_key",
        )

    st.write("")

    # ── Fetch & display forecast ───────────────────────────────────────────────
    forecast = None
    if api_key:
        with st.spinner(T["wx_fetching"]):
            forecast = fetch_forecast(api_key)

    if forecast:
        # ── Alerts first ──────────────────────────────────────────────────────
        st.subheader(T["alert_header"])

        min_temps  = [v["min"]  for v in forecast.values()]
        rain_total = sum(v["rain"] for v in forecast.values())
        frost_risk = any(t < FROST_THRESHOLD_C for t in min_temps)
        hw_open    = harvest_window_open()
        high_rain  = rain_total > 40  # mm over 7 days

        if frost_risk:
            st.markdown(
                f'<div class="alert-box frost-alert">'
                f'<strong>{T["frost_alert"]}</strong><br>'
                f'<span style="font-size:0.9rem">{T["frost_detail"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.success(
                "✅ No frost risk in the next 7 days — pruning conditions are safe."
                if lang == "en" else
                "✅ Nessun rischio gelata nei prossimi 7 giorni — condizioni di potatura sicure."
            )

        if hw_open:
            css_class = "harvest-open" if not high_rain else "harvest-wait"
            hw_msg    = T["harvest_open"] if not high_rain else T["harvest_wait"]
            detail    = "" if not high_rain else f"<br><small>{T['harvest_rain']}</small>"
            st.markdown(
                f'<div class="alert-box {css_class}">'
                f'<strong>{hw_msg}</strong>{detail}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            next_hw = datetime.date(
                datetime.date.today().year, HARVEST_START_MONTH, HARVEST_START_DAY
            )
            days_to_hw = (next_hw - datetime.date.today()).days
            st.info(
                f"🍂 Harvest window opens **Oct 15** — {days_to_hw} days to go. {T['harvest_logic']}"
                if lang == "en" else
                f"🍂 La finestra di raccolta apre il **15 ottobre** — mancano {days_to_hw} giorni. {T['harvest_logic']}"
            )

        st.write("")

        # ── 7-day table ───────────────────────────────────────────────────────
        st.subheader(f"📅 {T['wx_7day']}")
        wx_rows = []
        for day, v in forecast.items():
            wx_rows.append({
                T["wx_col_date"]:  day.strftime("%a %d %b"),
                T["wx_col_desc"]:  v["desc"],
                T["wx_col_max"]:   f"{v['max']:.1f}",
                T["wx_col_min"]:   f"{v['min']:.1f}",
                T["wx_col_rain"]:  f"{v['rain']:.1f}",
                T["wx_col_wind"]:  f"{v['wind']:.0f}",
            })
        st.table(wx_rows)

        # ── Mini spark-chart of temperatures ─────────────────────────────────
        import pandas as pd
        chart_df = pd.DataFrame([
            {"Day": d.strftime("%d %b"), "Max °C": v["max"], "Min °C": v["min"]}
            for d, v in forecast.items()
        ]).set_index("Day")
        st.line_chart(chart_df, color=["#e05c2d", "#3a86cc"])

    else:
        # Demo mode
        st.info(T["wx_demo"])

        # Static alert demo so UI isn't empty
        st.subheader(T["alert_header"])

        hw_open = harvest_window_open()
        st.markdown(
            f'<div class="alert-box frost-alert">'
            f'<strong>{T["frost_alert"]}</strong><br>'
            f'<em>(Demo — connect API for live data)</em>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if hw_open:
            st.markdown(
                f'<div class="alert-box harvest-open">'
                f'<strong>{T["harvest_open"]}</strong><br>'
                f'<em>(Demo)</em>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            next_hw    = datetime.date(datetime.date.today().year, HARVEST_START_MONTH, HARVEST_START_DAY)
            days_to_hw = (next_hw - datetime.date.today()).days
            st.info(
                f"🍂 Harvest window opens **Oct 15** — {days_to_hw} days away. (Demo mode)"
                if lang == "en" else
                f"🍂 Finestra raccolta: **15 ottobre** — {days_to_hw} giorni. (Modalità demo)"
            )

        if api_key:
            st.error(T["wx_error"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BIOLOGICAL RISK MONITOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == T["bio_nav"]:

    st.header(f"🪰 {T['bio_header']}")
    st.markdown(T["bio_intro"])
    st.divider()

    # ── Re-use cached forecast if available ───────────────────────────────────
    api_key_bio = ""
    try:
        api_key_bio = st.secrets["OWM_API_KEY"]
    except Exception:
        pass
    if not api_key_bio:
        api_key_bio = st.session_state.get("owm_key", "")

    forecast_bio = fetch_forecast(api_key_bio) if api_key_bio else None

    # ── Compute risk from forecast or fall back to demo values ────────────────
    if forecast_bio:
        avg_temps    = [(v["max"] + v["min"]) / 2 for v in forecast_bio.values()]
        avg_humidity = sum(v["humidity"] for v in forecast_bio.values()) / len(forecast_bio)
        week_avg_t   = sum(avg_temps) / len(avg_temps)
        is_live      = True
    else:
        # Demo values — typical Ligurian late-summer scenario
        week_avg_t   = 22.5
        avg_humidity = 62.0
        is_live      = False
        st.info(T["bio_wx_demo"])

    # ── Risk classification ───────────────────────────────────────────────────
    if week_avg_t < 15.0 or week_avg_t > 32.0:
        risk_level  = "low"
        risk_pct    = 20
        bar_color   = "#28a745"
        bar_label   = T["bio_low"]
        risk_why    = T["bio_low_why"]
        css_class   = "risk-low"
    elif 15.0 <= week_avg_t <= 20.0:
        risk_level  = "medium"
        risk_pct    = 55
        bar_color   = "#f0a500"
        bar_label   = T["bio_medium"]
        risk_why    = T["bio_medium_why"]
        css_class   = "risk-medium"
    elif 20.0 < week_avg_t <= 30.0 and avg_humidity > 50.0:
        risk_level  = "high"
        risk_pct    = 90
        bar_color   = "#dc3545"
        bar_label   = T["bio_high"]
        risk_why    = T["bio_high_why"]
        css_class   = "risk-high"
    else:
        # Temp in 20–30 range but humidity ≤ 50 % → medium-high
        risk_level  = "medium"
        risk_pct    = 68
        bar_color   = "#f0a500"
        bar_label   = T["bio_medium"]
        risk_why    = T["bio_medium_why"]
        css_class   = "risk-medium"

    # ── Status layout ─────────────────────────────────────────────────────────
    col_risk, col_meta = st.columns([2, 1])

    with col_risk:
        st.subheader(T["bio_risk_label"])

        # Color-coded progress bar
        st.markdown(
            f'<div class="risk-bar-wrap">'
            f'<div class="risk-bar-fill" style="width:{risk_pct}%;background:{bar_color};color:white;">'
            f'&nbsp;{bar_label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Narrative box
        st.markdown(
            f'<div class="alert-box {css_class}">'
            f'<strong>{bar_label}</strong><br>'
            f'<span style="font-size:0.9rem">{risk_why}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # High-risk actionable advice (bilingual inline)
        if risk_level == "high":
            st.error(
                f"**EN:** {T['bio_advice_high']}\n\n"
                f"**IT:** {LANG['it']['bio_advice_high']}"
                if lang == "en" else
                f"**IT:** {T['bio_advice_high']}\n\n"
                f"**EN:** {LANG['en']['bio_advice_high']}"
            )

    with col_meta:
        st.subheader("📊 " + ("Weather Inputs" if lang == "en" else "Dati meteo"))
        src = "🔴 Live" if is_live else "⚪ Demo"
        st.metric("Source / Fonte", src)
        st.metric("Avg Temp (7d)", f"{week_avg_t:.1f} °C")
        st.metric("Avg Humidity", f"{avg_humidity:.0f} %")

    st.divider()

    # ── Per-day risk breakdown (live only) ───────────────────────────────────
    if forecast_bio:
        import pandas as pd
        st.subheader("📅 " + ("Daily Risk Profile" if lang == "en" else "Profilo giornaliero"))

        day_rows = []
        for d, v in forecast_bio.items():
            day_avg  = (v["max"] + v["min"]) / 2
            day_hum  = v["humidity"]
            if day_avg < 15 or day_avg > 32:
                day_risk = T["bio_low"]
                day_col  = "🟢"
            elif 15 <= day_avg <= 20:
                day_risk = T["bio_medium"]
                day_col  = "🟡"
            elif 20 < day_avg <= 30 and day_hum > 50:
                day_risk = T["bio_high"]
                day_col  = "🔴"
            else:
                day_risk = T["bio_medium"]
                day_col  = "🟡"

            day_rows.append({
                ("Date" if lang == "en" else "Data"):     d.strftime("%a %d %b"),
                ("Avg °C" if lang == "en" else "°C med"): f"{day_avg:.1f}",
                ("Humidity" if lang == "en" else "Umidità"): f"{day_hum} %",
                ("Risk Level" if lang == "en" else "Livello"):  f"{day_col} {day_risk}",
            })
        st.table(day_rows)

    st.divider()

    # ── Threshold reference table ─────────────────────────────────────────────
    st.subheader(f"📋 {T['bio_thresholds']}")
    ref_rows = [
        {"🚦": "🟢", ("Condition" if lang == "en" else "Condizione"): T["bio_th_low"],  ("Level" if lang == "en" else "Livello"): T["bio_th_low_l"]},
        {"🚦": "🟡", ("Condition" if lang == "en" else "Condizione"): T["bio_th_med"],  ("Level" if lang == "en" else "Livello"): T["bio_th_med_l"]},
        {"🚦": "🔴", ("Condition" if lang == "en" else "Condizione"): T["bio_th_high"], ("Level" if lang == "en" else "Livello"): T["bio_th_high_l"]},
    ]
    st.table(ref_rows)

    st.divider()

    # ── Protection Cost Estimator ─────────────────────────────────────────────
    st.subheader(f"💶 {T['bio_cost_header']}")
    st.markdown(T["bio_cost_intro"])

    TREES        = TREE_BASELINE          # 310
    L_PER_TREE   = 3.0
    TOTAL_L      = TREES * L_PER_TREE     # 930 L per full coverage

    # Organic copper (Bordeaux mixture) at 1 % → 1 kg copper sulfate per 100 L
    COPPER_KG    = (TOTAL_L / 100) * 1.0  # 9.30 kg

    # Kaolin clay at 3 % → 3 kg per 100 L
    KAOLIN_KG    = (TOTAL_L / 100) * 3.0  # 27.9 kg

    # Typical season: 2–4 applications
    COVERAGES_LO = 2
    COVERAGES_HI = 4

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T["bio_cost_total_l"],    f"{TOTAL_L:.0f} L")
    c2.metric(T["bio_cost_copper_l"],   f"{COPPER_KG:.1f} kg / coverage")
    c3.metric(T["bio_cost_kaolin_l"],   f"{KAOLIN_KG:.1f} kg / coverage")
    c4.metric(T["bio_cost_coverages"],  f"{COVERAGES_LO}–{COVERAGES_HI} × / season")

    # Season totals
    st.write("")
    s1, s2 = st.columns(2)
    with s1:
        st.info(
            f"**Copper season total:** {COPPER_KG * COVERAGES_LO:.1f} – "
            f"{COPPER_KG * COVERAGES_HI:.1f} kg  "
            f"({TOTAL_L * COVERAGES_LO:.0f} – {TOTAL_L * COVERAGES_HI:.0f} L solution)"
            if lang == "en" else
            f"**Rame totale stagione:** {COPPER_KG * COVERAGES_LO:.1f} – "
            f"{COPPER_KG * COVERAGES_HI:.1f} kg  "
            f"({TOTAL_L * COVERAGES_LO:.0f} – {TOTAL_L * COVERAGES_HI:.0f} L soluzione)"
        )
    with s2:
        st.info(
            f"**Kaolin season total:** {KAOLIN_KG * COVERAGES_LO:.1f} – "
            f"{KAOLIN_KG * COVERAGES_HI:.1f} kg  "
            f"({TOTAL_L * COVERAGES_LO:.0f} – {TOTAL_L * COVERAGES_HI:.0f} L solution)"
            if lang == "en" else
            f"**Caolino totale stagione:** {KAOLIN_KG * COVERAGES_LO:.1f} – "
            f"{KAOLIN_KG * COVERAGES_HI:.1f} kg  "
            f"({TOTAL_L * COVERAGES_LO:.0f} – {TOTAL_L * COVERAGES_HI:.0f} L soluzione)"
        )

    st.caption(T["bio_cost_note"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INTERACTIVE MAP
# ══════════════════════════════════════════════════════════════════════════════
elif page == T["nav_map"]:

    st.header(f"🗺️ {T['map_header']}")
    st.caption(T["map_caption"])

    # ── Coordinate geometry ───────────────────────────────────────────────────
    # At lat 44.2445°: 1 m ≈ 0.000008983° lat  |  1 m ≈ 0.000012531° lon
    # Plots are arranged as adjacent terraced strips running E→W along the
    # hillside at Località Crovetta.  Widths are proportional to each plot's
    # actual Visura area (66 m N–S depth for all plots).
    #
    #  |← 2671 →|←——— 2675 ———→|←——————— 2677 ———————→|←——— 2679 ———→|
    #   19 m      55 m            80 m                   50 m
    #  1 266 m²   3 608 m²        5 302 m²               3 274 m²
    #
    # Total width ≈ 204 m  ×  66 m depth  =  13 464 m²  ≈ 1.345 ha ✓

    _LAT_M = 0.000008983   # degrees per metre (latitude)
    _LON_M = 0.000012531   # degrees per metre (longitude)

    DEPTH_M = 66.0         # N–S depth of all plots (metres)
    half_d  = DEPTH_M / 2

    # West-edge longitude (102 m west of centre)
    WEST_LON = MONEGLIA_LON - 102 * _LON_M
    NORTH_LAT = MONEGLIA_LAT + half_d * _LAT_M
    SOUTH_LAT = MONEGLIA_LAT - half_d * _LAT_M

    # Each plot's E–W width in metres
    plot_widths_m = {
        "2671": 19.0,
        "2675": 55.0,
        "2677": 80.0,
        "2679": 50.0,
    }
    plot_colors = {
        "2671": "#4a7c59",   # dark olive green  (Uliveto)
        "2675": "#c4a035",   # amber/gold        (Sem Irr Arb)
        "2677": "#3a6b45",   # deep green        (Uliveto, largest)
        "2679": "#5e9e72",   # medium green      (Uliveto)
    }
    plot_fill = {
        "2671": "#6aaa7e",
        "2675": "#f0d080",
        "2677": "#7ecb96",
        "2679": "#90d4a8",
    }
    plot_qualita = {
        "2671": "Uliveto",
        "2675": "Sem Irr Arb",
        "2677": "Uliveto",
        "2679": "Uliveto",
    }

    # Build polygons
    cursor_lon = WEST_LON
    plot_centroids = {}

    m = folium.Map(
        location=[MONEGLIA_LAT, MONEGLIA_LON],
        zoom_start=18,
        tiles="OpenStreetMap",
    )

    # Satellite tile layer
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery",
        name="🛰 Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    for mappale, width_m in plot_widths_m.items():
        w_deg = width_m * _LON_M
        east_lon  = cursor_lon + w_deg
        mid_lon   = cursor_lon + w_deg / 2
        mid_lat   = MONEGLIA_LAT
        plot_centroids[mappale] = (mid_lat, mid_lon)

        area_m2 = {"2671": 1_266, "2675": 3_608, "2677": 5_302, "2679": 3_274}[mappale]
        qualita = plot_qualita[mappale]
        trees_txt = (
            f"~{round((area_m2/10000)*230)} trees"
            if qualita == "Uliveto" else "arable/mixed"
        )

        poly_coords = [
            [NORTH_LAT, cursor_lon],
            [NORTH_LAT, east_lon],
            [SOUTH_LAT, east_lon],
            [SOUTH_LAT, cursor_lon],
        ]

        popup_html = (
            f"<b>Mappale {mappale}</b><br>"
            f"Qualità: {qualita}<br>"
            f"Area: {area_m2:,} m²  ({area_m2/10000:.4f} ha)<br>"
            f"Olivi / Trees: {trees_txt}"
        )

        folium.Polygon(
            locations=poly_coords,
            color=plot_colors[mappale],
            weight=2,
            fill=True,
            fill_color=plot_fill[mappale],
            fill_opacity=0.45,
            tooltip=f"Mappale {mappale} — {qualita} — {area_m2:,} m²",
            popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)

        # Plot number label as DivIcon
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(
                html=(
                    f'<div style="'
                    f'font-size:11px;font-weight:bold;color:#1a1a1a;'
                    f'background:rgba(255,255,255,0.78);'
                    f'border:1px solid {plot_colors[mappale]};'
                    f'border-radius:4px;padding:2px 5px;'
                    f'white-space:nowrap;text-align:center;">'
                    f'{mappale}<br>'
                    f'<span style="font-size:9px;font-weight:normal">{area_m2:,} m²</span>'
                    f'</div>'
                ),
                icon_size=(72, 32),
                icon_anchor=(36, 16),
            ),
        ).add_to(m)

        cursor_lon = east_lon  # advance to next plot

    # ── Combined boundary polygon (outline only) ──────────────────────────────
    EAST_LON = cursor_lon
    outer_coords = [
        [NORTH_LAT, WEST_LON],
        [NORTH_LAT, EAST_LON],
        [SOUTH_LAT, EAST_LON],
        [SOUTH_LAT, WEST_LON],
    ]
    folium.Polygon(
        locations=outer_coords,
        color="#1a4a2e",
        weight=3,
        fill=False,
        tooltip="Foglio 13 — Total grove boundary",
    ).add_to(m)

    # ── Master label marker at centroid ──────────────────────────────────────
    centre_lon = (WEST_LON + EAST_LON) / 2
    folium.Marker(
        location=[SOUTH_LAT - 0.00018, centre_lon],
        icon=folium.DivIcon(
            html=(
                '<div style="'
                'font-size:13px;font-weight:bold;color:#1a4a2e;'
                'background:rgba(255,255,255,0.92);'
                'border:2px solid #1a4a2e;border-radius:6px;'
                'padding:5px 10px;white-space:nowrap;text-align:center;'
                'box-shadow:0 2px 6px rgba(0,0,0,0.2);">'
                '🫒 Total Area: 1.34 Ha — 310 Olive Trees'
                '</div>'
            ),
            icon_size=(310, 36),
            icon_anchor=(155, 0),
        ),
    ).add_to(m)

    # ── Residence & storage markers (near grove, plausible offset) ───────────
    folium.Marker(
        location=[MONEGLIA_LAT + 0.00045, MONEGLIA_LON - 0.00090],
        tooltip=T["map_residence"],
        popup=folium.Popup(
            "<b>🏠 Residenza principale</b><br>Mappale 2670<br>8 vani", max_width=180
        ),
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)

    folium.Marker(
        location=[MONEGLIA_LAT - 0.00035, MONEGLIA_LON - 0.00070],
        tooltip=T["map_storage"],
        popup=folium.Popup(
            "<b>🏚 Depositi</b><br>Mappali 2673, 2674<br>116 m² totali", max_width=180
        ),
        icon=folium.Icon(color="orange", icon="archive", prefix="fa"),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(m, width="100%", height=580, returned_objects=[])

    st.write("")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("📍 Location", "Loc. Crovetta, Moneglia")
    col_b.metric("🟢 Grove plots", "2671 · 2675 · 2677 · 2679")
    col_c.metric("🔴 Residence", "Mappale 2670 · 8 rooms")
    col_d.metric("🟠 Storage", "Mappali 2673–2674 · 116 m²")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SEASONAL TASKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == T["nav_tasks"]:

    st.header(f"📋 {T['tasks_header']}")
    st.info(T["tasks_note"])

    seasons_en = [
        ("🌱 Winter Prep (Jan–Feb)", [
            "Check irrigation pipes for frost damage",
            "Apply winter fertiliser",
            "Equipment maintenance & sharpening",
            "Annual planning & record review",
        ]),
        ("✂️ Spring Pruning (Mar–Apr)", [
            "Prune olive trees (avoid frost days!)",
            "Remove suckers & deadwood",
            "Apply foliar micronutrients",
            "Monitor for olive fly (Bactrocera oleae)",
        ]),
        ("🌞 Summer Care (May–Aug)", [
            "Weed control & mulching",
            "Irrigation schedule review",
            "Pest & disease monitoring",
            "Prepare nets & harvest equipment",
        ]),
        ("🍂 Harvest (Oct 15 – Nov)", [
            "Place harvest nets under trees",
            "Hand-pick or mechanical harvest",
            "Transport to Frantoio within 24 h",
            "Record yield per mappale",
            "Post-harvest fertilisation",
        ]),
    ]
    seasons_it = [
        ("🌱 Preparazione invernale (Gen–Feb)", [
            "Controllare impianto irrigazione (danni da gelo)",
            "Concimazione invernale",
            "Manutenzione attrezzatura",
            "Pianificazione annuale e revisione registri",
        ]),
        ("✂️ Potatura primaverile (Mar–Apr)", [
            "Potare gli ulivi (evitare giorni di gelo!)",
            "Eliminare polloni e rami secchi",
            "Applicare micronutrienti fogliari",
            "Monitorare la mosca dell'olivo (Bactrocera oleae)",
        ]),
        ("🌞 Cura estiva (Mag–Ago)", [
            "Diserbo e pacciamatura",
            "Revisione programma irrigazione",
            "Monitoraggio parassiti e malattie",
            "Preparare reti e attrezzatura per raccolta",
        ]),
        ("🍂 Raccolta (15 Ott – Nov)", [
            "Posizionare le reti sotto gli alberi",
            "Raccolta manuale o meccanica",
            "Consegna al Frantoio entro 24 h",
            "Registrare la resa per mappale",
            "Concimazione post-raccolta",
        ]),
    ]

    seasons = seasons_it if lang == "it" else seasons_en
    col_pairs = st.columns(2)

    for idx, (season_name, tasks) in enumerate(seasons):
        with col_pairs[idx % 2]:
            st.markdown(f"**{season_name}**")
            for task in tasks:
                st.checkbox(task, key=f"task_{idx}_{task[:20]}")
            st.write("")

    st.divider()
    st.caption(T["footer"])


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.caption(T["footer"])
