"""
Olive Grove Management App — Moneglia, Italy
=============================================
Requirements:
    pip install streamlit folium streamlit-folium

Run:
    streamlit run olive_grove_app.py
"""

import streamlit as st
import folium
from streamlit_folium import st_folium

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Olive Grove Manager | Moneglia",
    page_icon="🫒",
    layout="wide",
)

# ── Translations ──────────────────────────────────────────────────────────────
LANG = {
    "en": {
        "app_title": "🫒 Olive Grove Manager",
        "app_subtitle": "Moneglia, Liguria — Italy",
        "sidebar_title": "Settings",
        "lang_label": "Language / Lingua",
        "nav_label": "Navigation",
        "nav_overview": "Grove Overview",
        "nav_map": "Interactive Map",
        "nav_tasks": "Tasks & Notes",
        "overview_header": "Grove Overview",
        "overview_intro": (
            "Your olive grove is located in Moneglia (GE), registered on "
            "**Foglio n. 13** of the Catasto Terreni."
        ),
        "total_area": "Total Surface Area",
        "total_area_val": "≈ 1.3 hectares (13,000 m²)",
        "num_plots": "Number of Plots",
        "num_plots_val": "4 cadastral parcels",
        "foglio": "Foglio",
        "foglio_val": "n. 13",
        "municipality": "Municipality",
        "municipality_val": "Moneglia (GE), Liguria",
        "plots_table_header": "📋 Cadastral Parcels — Foglio n. 13",
        "col_parcel": "Parcel (Mappale)",
        "col_desc": "Description",
        "col_area": "Est. Area",
        "col_trees": "Est. Olive Trees",
        "plot_desc": "Olive grove — terraced hillside",
        "map_header": "Interactive Map",
        "map_caption": (
            "Map centred on Moneglia, Liguria. "
            "Adjust zoom to explore the grove area."
        ),
        "map_marker": "Olive Grove — Moneglia (Foglio 13)",
        "map_marker_popup": (
            "<b>🫒 Olive Grove</b><br>"
            "Foglio n. 13<br>"
            "Parcels: 2671, 2675, 2677, 2679<br>"
            "Area: ≈ 1.3 ha"
        ),
        "tasks_header": "Tasks & Notes",
        "tasks_note": (
            "Use this section to track seasonal activities for your grove."
        ),
        "tasks_coming": "📝 Task tracker coming soon — stay tuned!",
        "footer": "Built with Streamlit · Olive Grove Manager v1.0",
    },
    "it": {
        "app_title": "🫒 Gestione Uliveto",
        "app_subtitle": "Moneglia, Liguria — Italia",
        "sidebar_title": "Impostazioni",
        "lang_label": "Lingua / Language",
        "nav_label": "Navigazione",
        "nav_overview": "Panoramica dell'uliveto",
        "nav_map": "Mappa interattiva",
        "nav_tasks": "Attività e Note",
        "overview_header": "Panoramica dell'uliveto",
        "overview_intro": (
            "Il tuo uliveto si trova a Moneglia (GE), registrato sul "
            "**Foglio n. 13** del Catasto Terreni."
        ),
        "total_area": "Superficie totale",
        "total_area_val": "≈ 1,3 ettari (13.000 m²)",
        "num_plots": "Numero di particelle",
        "num_plots_val": "4 particelle catastali",
        "foglio": "Foglio",
        "foglio_val": "n. 13",
        "municipality": "Comune",
        "municipality_val": "Moneglia (GE), Liguria",
        "plots_table_header": "📋 Particelle catastali — Foglio n. 13",
        "col_parcel": "Mappale",
        "col_desc": "Descrizione",
        "col_area": "Superficie stimata",
        "col_trees": "Olivi stimati",
        "plot_desc": "Uliveto — versante terrazzato",
        "map_header": "Mappa interattiva",
        "map_caption": (
            "Mappa centrata su Moneglia, Liguria. "
            "Usa lo zoom per esplorare l'area dell'uliveto."
        ),
        "map_marker": "Uliveto — Moneglia (Foglio 13)",
        "map_marker_popup": (
            "<b>🫒 Uliveto</b><br>"
            "Foglio n. 13<br>"
            "Mappali: 2671, 2675, 2677, 2679<br>"
            "Superficie: ≈ 1,3 ha"
        ),
        "tasks_header": "Attività e Note",
        "tasks_note": (
            "Usa questa sezione per tenere traccia delle attività stagionali."
        ),
        "tasks_coming": "📝 Gestore attività in arrivo — stay tuned!",
        "footer": "Creato con Streamlit · Gestione Uliveto v1.0",
    },
}

# ── Plot data ──────────────────────────────────────────────────────────────────
PLOTS = [
    {"mappale": "2671", "area_m2": 3100, "trees": 28},
    {"mappale": "2675", "area_m2": 3400, "trees": 31},
    {"mappale": "2677", "area_m2": 3250, "trees": 29},
    {"mappale": "2679", "area_m2": 3250, "trees": 30},
]

MONEGLIA_LAT = 44.238
MONEGLIA_LON = 9.491

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ " + "Settings / Impostazioni")
    st.divider()

    lang_choice = st.radio(
        "🌐 Language / Lingua",
        options=["English 🇬🇧", "Italiano 🇮🇹"],
        index=0,
    )
    lang = "it" if "Italiano" in lang_choice else "en"
    T = LANG[lang]

    st.divider()
    page = st.radio(
        T["nav_label"],
        options=[T["nav_overview"], T["nav_map"], T["nav_tasks"]],
    )
    st.divider()
    st.caption("📍 Moneglia (GE), Liguria")
    st.caption("🗺️ Foglio n. 13 · 4 mappali · ≈ 1.3 ha")

# ── App title ─────────────────────────────────────────────────────────────────
st.title(T["app_title"])
st.markdown(f"*{T['app_subtitle']}*")
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Grove Overview
# ══════════════════════════════════════════════════════════════════════════════
if page == T["nav_overview"]:
    st.header(f"🌿 {T['overview_header']}")
    st.markdown(T["overview_intro"])
    st.write("")

    # Summary metric cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(T["total_area"], T["total_area_val"])
    with col2:
        st.metric(T["num_plots"], T["num_plots_val"])
    with col3:
        st.metric(T["foglio"], T["foglio_val"])
    with col4:
        st.metric(T["municipality"], T["municipality_val"])

    st.write("")
    st.subheader(T["plots_table_header"])

    # Build parcels table
    table_data = []
    for p in PLOTS:
        table_data.append({
            T["col_parcel"]: p["mappale"],
            T["col_desc"]: T["plot_desc"],
            T["col_area"]: f"{p['area_m2']:,} m²  (~{p['area_m2']/10000:.2f} ha)",
            T["col_trees"]: f"~{p['trees']}",
        })

    st.table(table_data)

    # Total row
    total_m2 = sum(p["area_m2"] for p in PLOTS)
    total_trees = sum(p["trees"] for p in PLOTS)
    st.info(
        f"**Total:** {total_m2:,} m²  ≈ {total_m2/10000:.2f} ha  ·  "
        f"~{total_trees} olive trees across all parcels"
        if lang == "en" else
        f"**Totale:** {total_m2:,} m²  ≈ {total_m2/10000:.2f} ha  ·  "
        f"~{total_trees} olivi complessivi"
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Interactive Map
# ══════════════════════════════════════════════════════════════════════════════
elif page == T["nav_map"]:
    st.header(f"🗺️ {T['map_header']}")
    st.caption(T["map_caption"])

    m = folium.Map(
        location=[MONEGLIA_LAT, MONEGLIA_LON],
        zoom_start=15,
        tiles="OpenStreetMap",
    )

    # Main grove marker
    folium.Marker(
        location=[MONEGLIA_LAT, MONEGLIA_LON],
        popup=folium.Popup(T["map_marker_popup"], max_width=220),
        tooltip=T["map_marker"],
        icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
    ).add_to(m)

    # Approximate grove boundary circle (radius ≈ 65 m → ~1.3 ha)
    folium.Circle(
        location=[MONEGLIA_LAT, MONEGLIA_LON],
        radius=65,
        color="#4a7c59",
        fill=True,
        fill_color="#6aaa7e",
        fill_opacity=0.25,
        tooltip="≈ 1.3 ha grove area",
    ).add_to(m)

    # Layer control + scale
    folium.LayerControl().add_to(m)

    # Render map
    st_folium(m, width="100%", height=520, returned_objects=[])

    st.write("")
    st.markdown(
        "**Coordinates:** `44.238° N, 9.491° E`  ·  "
        "Moneglia, Province of Genova, Liguria 🇮🇹"
        if lang == "en" else
        "**Coordinate:** `44.238° N, 9.491° E`  ·  "
        "Moneglia, Provincia di Genova, Liguria 🇮🇹"
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Tasks & Notes
# ══════════════════════════════════════════════════════════════════════════════
elif page == T["nav_tasks"]:
    st.header(f"📋 {T['tasks_header']}")
    st.info(T["tasks_note"])

    # Seasonal task checklist (static placeholder)
    st.subheader("🗓️ Seasonal Calendar" if lang == "en" else "🗓️ Calendario stagionale")

    seasons = (
        [
            ("🌸 Spring (Mar–May)", ["Pruning", "Fertilising", "Pest monitoring"]),
            ("☀️ Summer (Jun–Aug)", ["Irrigation check", "Weed control", "Net preparation"]),
            ("🍂 Harvest (Sep–Nov)", ["Net placement", "Olive harvest", "Transport to mill"]),
            ("❄️ Winter (Dec–Feb)", ["Soil work", "Equipment maintenance", "Planning"]),
        ]
        if lang == "en" else
        [
            ("🌸 Primavera (Mar–Mag)", ["Potatura", "Concimazione", "Monitoraggio parassiti"]),
            ("☀️ Estate (Giu–Ago)", ["Controllo irrigazione", "Diserbo", "Preparazione reti"]),
            ("🍂 Raccolta (Set–Nov)", ["Posizionamento reti", "Raccolta olive", "Trasporto al frantoio"]),
            ("❄️ Inverno (Dic–Feb)", ["Lavori al suolo", "Manutenzione attrezzatura", "Pianificazione"]),
        ]
    )

    cols = st.columns(2)
    for i, (season, tasks) in enumerate(seasons):
        with cols[i % 2]:
            st.markdown(f"**{season}**")
            for task in tasks:
                st.checkbox(task, key=f"{season}_{task}")
            st.write("")

    st.caption(T["tasks_coming"])

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(T["footer"])
