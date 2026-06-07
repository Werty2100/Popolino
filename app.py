import streamlit as st
import pandas as pd
from firebase_config import init_firebase
from datetime import date

# Connessione Firebase
db = init_firebase()

# Configurazione pagina
st.set_page_config(
    page_title="Popolino",
    page_icon="",
    layout="wide"
)

# Lista amici
AMICI = ["AntonioB.", "Massimo", "Mario", "Joele", "Vincenzo", "AntonioR.", "Giovanni"]

# ── SIDEBAR ──────────────────────────────────────
st.sidebar.title("Popolino")
pagina = st.sidebar.selectbox("Menu", [
    "🏠 Home",
    "➕ Aggiungi uscita",
    "📋 Storico uscite",
    "📊 Statistiche"
])

# ══════════════════════════════════════════════════
# PAGINA HOME
# ══════════════════════════════════════════════════
if pagina == "🏠 Home":
    st.title("Popolino")
    st.write("")

    uscite = db.collection("uscite").order_by("data", direction="DESCENDING").limit(3).get()

    st.subheader("Ultime 3 uscite")
    for s in uscite:
        dati = s.to_dict()
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {dati['data']}")
            with col2:
                presenti = sum(1 for a in AMICI if dati.get(f"presente_{a}"))
                st.metric("Presenti", f"{presenti}/{len(AMICI)}")
            with col3:
                voti = [dati.get(f"voto_{a}", 0) for a in AMICI if dati.get(f"presente_{a}")]
                media = round(sum(voti) / len(voti), 1) if voti else 0
                st.metric("Media voti", media)

# ══════════════════════════════════════════════════
# PAGINA AGGIUNGI USCITA
# ══════════════════════════════════════════════════
elif pagina == "➕ Aggiungi uscita":
    st.title("➕ Aggiungi un'uscita")

    if "dati_uscita" not in st.session_state:
        st.session_state.dati_uscita = {f"presente_{a}": False for a in AMICI}
        st.session_state.dati_uscita.update({f"voto_{a}": 0.0 for a in AMICI})

    data_uscita = st.date_input("Data", value=date.today())

    st.divider()
    st.subheader("Presenze e voti")

    for amico in AMICI:
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.markdown(f"**{amico}**")
        with col2:
            presente = st.checkbox(
                "Presente",
                key=f"pres_{amico}",
                value=st.session_state.dati_uscita[f"presente_{amico}"]
            )
            st.session_state.dati_uscita[f"presente_{amico}"] = presente
        with col3:
            if presente:
                voto = st.number_input(
                    "Voto",
                    min_value=1.0,
                    max_value=10.0,
                    value=st.session_state.dati_uscita[f"voto_{amico}"] if st.session_state.dati_uscita[f"voto_{amico}"] > 0 else 7.0,
                    step=0.25,
                    key=f"voto_{amico}"
                )
                st.session_state.dati_uscita[f"voto_{amico}"] = voto
            else:
                st.session_state.dati_uscita[f"voto_{amico}"] = 0.0
                st.caption("Assente")

    st.divider()

    # ── Valutazione serata ─────────────────────────
    st.subheader("La serata ha:")
    col1, col2 = st.columns(2)
    with col1:
        hittato = st.checkbox("💥 Hittato", key="hittato")
    with col2:
        gasato = st.checkbox("🔥 Gasato", key="gasato")

    st.divider()

    if st.button("💾 Salva uscita", width="stretch"):
        dati_da_salvare = dict(st.session_state.dati_uscita)
        dati_da_salvare["data"] = str(data_uscita)
        dati_da_salvare["hittato"] = hittato
        dati_da_salvare["gasato"] = gasato
        db.collection("uscite").add(dati_da_salvare)
        del st.session_state.dati_uscita
        st.success("Uscita salvata! 🎉")

# ══════════════════════════════════════════════════
# PAGINA STORICO
# ══════════════════════════════════════════════════
elif pagina == "📋 Storico uscite":
    st.title("📋 Storico uscite")

    uscite = db.collection("uscite").order_by("data", direction="DESCENDING").get()

    if not uscite:
        st.info("Nessuna uscita ancora.")
    else:
        for s in uscite:
            dati = s.to_dict()
            presenti = [a for a in AMICI if dati.get(f"presente_{a}")]
            voti = [dati.get(f"voto_{a}", 0) for a in presenti]
            media = round(sum(voti) / len(voti), 1) if voti else 0

            with st.expander(f"🎉 Uscita del {dati['data']}"):
                col1, col2 = st.columns(2)
                col1.metric("⭐ Media voti", media)
                col2.metric("👥 Presenti", f"{len(presenti)}/{len(AMICI)}")

                # Badge hittato / gasato
                badges = []
                if dati.get("hittato"):
                    badges.append("💥 Hittato")
                if dati.get("gasato"):
                    badges.append("🔥 Gasato")
                if badges:
                    st.markdown("**La serata ha:** " + " &nbsp;|&nbsp; ".join(badges))

                st.divider()

                tabella = []
                for amico in AMICI:
                    tabella.append({
                        "Amico": amico,
                        "Presente": "✅" if dati.get(f"presente_{amico}") else "❌",
                        "Voto": str(dati.get(f"voto_{amico}", "—")) if dati.get(f"presente_{amico}") else "—"
                    })
                st.dataframe(pd.DataFrame(tabella), hide_index=True, width="stretch")

# ══════════════════════════════════════════════════
# PAGINA STATISTICHE
# ══════════════════════════════════════════════════
elif pagina == "📊 Statistiche":
    st.title("📊 Statistiche")

    uscite = db.collection("uscite").order_by("data").get()

    if not uscite:
        st.info("Nessuna uscita ancora. Aggiungine una!")
    else:
        tutti_dati = [s.to_dict() for s in uscite]

        # ── Presenze totali
        st.subheader("👥 Presenze totali")
        amici_ordinati = sorted(AMICI)
        presenze = {a: sum(1 for d in tutti_dati if d.get(f"presente_{a}")) for a in amici_ordinati}

        cols = st.columns(len(amici_ordinati))
        for i, amico in enumerate(amici_ordinati):
            with cols[i]:
                st.metric(amico, presenze[amico])

        st.divider()

        # ── Grafico presenze
        st.subheader("📊 Grafico presenze")
        import plotly.graph_objects as go

        fig_presenze = go.Figure()
        fig_presenze.add_trace(go.Bar(
            x=amici_ordinati,
            y=[presenze[a] for a in amici_ordinati],
            marker_color="#4f8ef7"
        ))
        fig_presenze.update_layout(
            yaxis=dict(
                rangemode="nonnegative",
                range=[0, max(presenze.values()) + 1],
                tickmode="linear",
                dtick=1
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig_presenze, width="stretch")

        st.divider()

        # ── Media voti per persona
        st.subheader("⭐ Media voti per persona")
        medie = {}
        for a in amici_ordinati:
            voti = [d.get(f"voto_{a}", 0) for d in tutti_dati if d.get(f"presente_{a}")]
            medie[a] = round(sum(voti) / len(voti), 1) if voti else 0

        fig_medie = go.Figure()
        fig_medie.add_trace(go.Bar(
            x=amici_ordinati,
            y=[medie[a] for a in amici_ordinati],
            marker_color="#4fc97f"
        ))
        fig_medie.update_layout(
            yaxis=dict(
                rangemode="nonnegative",
                range=[0, 10],
                tickmode="linear",
                dtick=1
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig_medie, width="stretch")
