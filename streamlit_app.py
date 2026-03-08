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
        /* Table header */
        thead tr th { background:#4a7c59 !important; color:white !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS — Official Visura Catastale data
# ══════════════════════════════════════════════════════════════════════════════
MONEGLIA_LAT  = 44.238
MONEGLIA_LON  = 9.491
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

        # Map
        "map_header":     "Interactive Map",
        "map_caption":    "Map centred on Moneglia (Lat 44.238, Lon 9.491). Zoom in to explore your grove.",
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

        # Map
        "map_header":     "Mappa interattiva",
        "map_caption":    "Mappa centrata su Moneglia (Lat 44.238, Lon 9.491). Usa lo zoom per esplorare l'uliveto.",
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
    for slot in raw.get("list", []):
        dt   = datetime.datetime.fromtimestamp(slot["dt"])
        day  = dt.date()
        temp = slot["main"]
        rain = slot.get("rain", {}).get("3h", 0.0)
        wind = slot["wind"]["speed"] * 3.6  # m/s → km/h
        desc = slot["weather"][0]["description"].capitalize()
        if day not in days:
            days[day] = {"max": temp["temp_max"], "min": temp["temp_min"],
                         "rain": 0.0, "wind": wind, "desc": desc}
        else:
            days[day]["max"]  = max(days[day]["max"], temp["temp_max"])
            days[day]["min"]  = min(days[day]["min"], temp["temp_min"])
            days[day]["rain"] += rain
            days[day]["wind"] = max(days[day]["wind"], wind)

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
# PAGE: INTERACTIVE MAP
# ══════════════════════════════════════════════════════════════════════════════
elif page == T["nav_map"]:

    st.header(f"🗺️ {T['map_header']}")
    st.caption(T["map_caption"])

    m = folium.Map(
        location=[MONEGLIA_LAT, MONEGLIA_LON],
        zoom_start=16,
        tiles="OpenStreetMap",
    )

    # Satellite layer option
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    # Grove area circle (~207 m radius → 1.345 ha)
    folium.Circle(
        location=[MONEGLIA_LAT, MONEGLIA_LON],
        radius=207,
        color="#4a7c59",
        fill=True,
        fill_color="#6aaa7e",
        fill_opacity=0.20,
        tooltip=f"🫒 Grove area ≈ 1.3450 ha",
        popup=folium.Popup(T["map_popup"], max_width=240),
    ).add_to(m)

    # Grove marker
    folium.Marker(
        location=[MONEGLIA_LAT, MONEGLIA_LON],
        tooltip=T["map_grove"],
        popup=folium.Popup(T["map_popup"], max_width=240),
        icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
    ).add_to(m)

    # Residence marker (slightly offset)
    folium.Marker(
        location=[MONEGLIA_LAT + 0.0008, MONEGLIA_LON + 0.0008],
        tooltip=T["map_residence"],
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)

    # Storage marker
    folium.Marker(
        location=[MONEGLIA_LAT + 0.0005, MONEGLIA_LON - 0.0007],
        tooltip=T["map_storage"],
        icon=folium.Icon(color="orange", icon="archive", prefix="fa"),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(m, width="100%", height=560, returned_objects=[])

    st.write("")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🟢 Grove", "Mappali 2671–2679")
    col_b.metric("🔴 Residence", "Mappale 2670 · 8 rooms")
    col_c.metric("🟠 Storage", "Mappali 2673–2674 · 116 m²")


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
