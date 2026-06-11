import streamlit as st
import pandas as pd
from firebase_config import init_firebase
from datetime import date, datetime

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
    "✍️ Modifica uscita",
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
                titolo = dati.get("titolo", "")
                if titolo:
                    st.caption(titolo)
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

    # ── Titolo opzionale ───────────────────────────
    st.divider()
    aggiungi_titolo = st.checkbox("Aggiungi un titolo alla serata", key="add_titolo")
    titolo_uscita = ""
    if aggiungi_titolo:
        titolo_uscita = st.text_input("Titolo", placeholder="Es. Serata pizza, Capodanno...", key="titolo_input")

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
        hittato = st.checkbox("Hittato", key="hittato")
    with col2:
        gasato = st.checkbox("Gasato", key="gasato")

    st.divider()

    if st.button("💾 Salva uscita", width="stretch"):
        dati_da_salvare = dict(st.session_state.dati_uscita)
        dati_da_salvare["data"] = str(data_uscita)
        dati_da_salvare["hittato"] = hittato
        dati_da_salvare["gasato"] = gasato if hittato else False
        dati_da_salvare["titolo"] = titolo_uscita.strip() if aggiungi_titolo else ""
        db.collection("uscite").add(dati_da_salvare)
        del st.session_state.dati_uscita
        st.success("Uscita salvata! 🎉")

# ══════════════════════════════════════════════════
# PAGINA MODIFICA USCITA
# ══════════════════════════════════════════════════
elif pagina == "✍️ Modifica uscita":
    st.title("✍️ Modifica uscita")

    uscite = db.collection("uscite").order_by("data", direction="DESCENDING").get()

    if not uscite:
        st.info("Nessuna uscita da modificare.")
    else:
        opzioni = {s.id: s.to_dict() for s in uscite}
        uscita_id = st.selectbox(
            "Seleziona l'uscita da modificare",
            options=list(opzioni.keys()),
            format_func=lambda x: opzioni[x]["data"]
        )

        # Se l'uscita selezionata è cambiata, pulisci tutte le key della vecchia
        if st.session_state.get("mod_uscita_id_corrente") != uscita_id:
            vecchio_id = st.session_state.get("mod_uscita_id_corrente")
            if vecchio_id:
                for key in list(st.session_state.keys()):
                    if key.startswith(f"mod_pres_{vecchio_id}") or                        key.startswith(f"mod_voto_{vecchio_id}") or                        key in (f"mod_hittato_{vecchio_id}", f"mod_gasato_{vecchio_id}",
                               f"mod_has_titolo_{vecchio_id}", f"mod_titolo_{vecchio_id}",
                               f"mod_data_{vecchio_id}"):
                        del st.session_state[key]
            st.session_state["mod_uscita_id_corrente"] = uscita_id

        dati = opzioni[uscita_id]

        st.divider()

        data_attuale = datetime.strptime(dati["data"], "%Y-%m-%d").date()
        data_uscita = st.date_input("Data", value=data_attuale, key=f"mod_data_{uscita_id}")

        # ── Titolo opzionale ───────────────────────
        st.divider()
        key_has_titolo = f"mod_has_titolo_{uscita_id}"
        key_titolo = f"mod_titolo_{uscita_id}"
        titolo_esistente = dati.get("titolo", "")

        if key_has_titolo not in st.session_state:
            st.session_state[key_has_titolo] = bool(titolo_esistente)
        if key_titolo not in st.session_state:
            st.session_state[key_titolo] = titolo_esistente

        aggiungi_titolo = st.checkbox("Aggiungi un titolo alla serata", key=key_has_titolo)
        titolo_uscita = ""
        if aggiungi_titolo:
            titolo_uscita = st.text_input("Titolo", key=key_titolo, placeholder="Es. Serata pizza, Capodanno...")

        st.divider()
        st.subheader("Presenze e voti")

        nuovi_dati = {}

        for amico in AMICI:
            col1, col2, col3 = st.columns([2, 1, 3])
            with col1:
                st.markdown(f"**{amico}**")
            with col2:
                key_pres = f"mod_pres_{uscita_id}_{amico}"
                if key_pres not in st.session_state:
                    st.session_state[key_pres] = dati.get(f"presente_{amico}", False)
                presente = st.checkbox("Presente", key=key_pres)
                nuovi_dati[f"presente_{amico}"] = presente
            with col3:
                if presente:
                    key_voto = f"mod_voto_{uscita_id}_{amico}"
                    if key_voto not in st.session_state:
                        voto_salvato = dati.get(f"voto_{amico}", 7.0)
                        st.session_state[key_voto] = float(voto_salvato) if voto_salvato and voto_salvato > 0 else 7.0
                    voto = st.number_input(
                        "Voto",
                        min_value=1.0,
                        max_value=10.0,
                        step=0.25,
                        key=key_voto
                    )
                    nuovi_dati[f"voto_{amico}"] = voto
                else:
                    nuovi_dati[f"voto_{amico}"] = 0.0
                    st.caption("Assente")

        st.divider()

        st.subheader("La serata ha:")
        col1, col2 = st.columns(2)
        with col1:
            key_hit = f"mod_hittato_{uscita_id}"
            if key_hit not in st.session_state:
                st.session_state[key_hit] = dati.get("hittato", False)
            hittato = st.checkbox("Hittato", key=key_hit)
        with col2:
            key_gas = f"mod_gasato_{uscita_id}"
            if key_gas not in st.session_state:
                st.session_state[key_gas] = dati.get("gasato", False)
            gasato = st.checkbox("Gasato", key=key_gas)

        st.divider()

        if st.button("💾 Salva modifiche", width="stretch"):
            nuovi_dati["data"] = str(data_uscita)
            nuovi_dati["hittato"] = hittato
            nuovi_dati["gasato"] = gasato if hittato else False
            nuovi_dati["titolo"] = titolo_uscita.strip() if aggiungi_titolo else ""
            db.collection("uscite").document(uscita_id).set(nuovi_dati, merge=True)
            st.success("Uscita modificata! ✅")

        st.divider()

        # ── Zona pericolosa: eliminazione ─────────
        with st.expander("🗑️ Elimina questa uscita"):
            label_uscita = dati.get("titolo") or dati["data"]
            st.warning(f"Stai per eliminare definitivamente **{label_uscita}**. Questa azione è irreversibile.")

            key_conferma = f"conferma_elimina_{uscita_id}"

            st.checkbox("Confermo di voler eliminare questa uscita", key=key_conferma)

            if st.button("🗑️ Elimina uscita", disabled=not st.session_state.get(key_conferma, False), type="primary"):
                db.collection("uscite").document(uscita_id).delete()
                st.success("Uscita eliminata.")
                st.switch_page("app.py")

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
            titolo = dati.get("titolo", "")
            label_expander = f"🎉 {titolo} — {dati['data']}" if titolo else f"🎉 Uscita del {dati['data']}"

            with st.expander(label_expander):
                col1, col2 = st.columns(2)
                col1.metric("⭐ Media voti", media)
                col2.metric("👥 Presenti", f"{len(presenti)}/{len(AMICI)}")

                hittato = dati.get("hittato", False)
                gasato = dati.get("gasato", False)

                if hittato and gasato:
                    st.markdown("**La serata ha hittato e gasato! 💥🔥**")
                elif hittato:
                    st.markdown("**La serata ha hittato! 💥**")

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
        tutti_dati = [{"id": s.id, **s.to_dict()} for s in uscite]

        # Calcola media per ogni uscita
        for d in tutti_dati:
            voti = [d.get(f"voto_{a}", 0) for a in AMICI if d.get(f"presente_{a}")]
            d["_media"] = round(sum(voti) / len(voti), 1) if voti else 0

        # ── Presenze totali ────────────────────────
        st.subheader("👥 Presenze totali")
        amici_ordinati = sorted(AMICI)
        presenze = {a: sum(1 for d in tutti_dati if d.get(f"presente_{a}")) for a in amici_ordinati}

        cols = st.columns(len(amici_ordinati))
        for i, amico in enumerate(amici_ordinati):
            with cols[i]:
                st.metric(amico, presenze[amico])

        st.divider()

        # ── Grafico presenze ───────────────────────
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

        # ── Media voti per persona ─────────────────
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

        st.divider()

        # ── Qualità delle serate ───────────────────
        st.subheader("🏆 Qualità delle serate")

        serate_10   = [d for d in tutti_dati if d["_media"] == 10.0]
        serate_8_9  = [d for d in tutti_dati if 8.0 <= d["_media"] < 10.0]
        serate_6_7  = [d for d in tutti_dati if 6.0 <= d["_media"] < 8.0]

        serate_hittato = [d for d in tutti_dati if d.get("hittato")]
        serate_gasato  = [d for d in tutti_dati if d.get("gasato")]

        col1, col2, col3 = st.columns(3)
        col1.metric("🌟 Media 10", len(serate_10))
        col2.metric("🔥 Media 8–9", len(serate_8_9))
        col3.metric("👍 Media 6–7", len(serate_6_7))

        col4, col5 = st.columns(2)
        col4.metric("💥 Serate hittate", len(serate_hittato))
        col5.metric("💥🔥 Serate hittate e gasate", len(serate_gasato))

        # Mostra le serate con media 10 se esistono
        if serate_10:
            st.markdown("**Serate con media 10:**")
            for d in serate_10:
                titolo = d.get("titolo", "")
                label = f"✨ {titolo} — {d['data']}" if titolo else f"✨ {d['data']}"
                st.caption(label)

        st.divider()

        # ── Top 3 serate del mese ──────────────────
        st.subheader("🥇 Top 3 serate del mese")

        # Ricava i mesi disponibili dalle uscite
        mesi_disponibili = sorted(
            set(d["data"][:7] for d in tutti_dati),
            reverse=True
        )

        mese_selezionato = st.selectbox(
            "Seleziona il mese",
            options=mesi_disponibili,
            format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%B %Y").capitalize()
        )

        serate_mese = [d for d in tutti_dati if d["data"].startswith(mese_selezionato)]

        if not serate_mese:
            st.info("Nessuna uscita in questo mese.")
        else:
            # Costruisci le opzioni per il multiselect (label → dati)
            def label_serata(d):
                titolo = d.get("titolo", "")
                return f"{titolo} — {d['data']}" if titolo else d["data"]

            opzioni_serate = {label_serata(d): d for d in serate_mese}

            # Recupera selezione salvata per questo mese
            key_top3 = f"top3_{mese_selezionato}"
            if key_top3 not in st.session_state:
                st.session_state[key_top3] = []

            selezionate = st.multiselect(
                "Scegli le 3 serate top (max 3)",
                options=list(opzioni_serate.keys()),
                default=st.session_state[key_top3],
                max_selections=3,
                key=key_top3
            )

            if selezionate:
                for i, label in enumerate(selezionate):
                    d = opzioni_serate[label]
                    medaglie = ["🥇", "🥈", "🥉"]
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            titolo = d.get("titolo", "")
                            st.markdown(f"{medaglie[i]} **{d['data']}**")
                            if titolo:
                                st.caption(titolo)
                            hittato = d.get("hittato", False)
                            gasato = d.get("gasato", False)
                            if hittato and gasato:
                                st.caption("💥🔥 Ha hittato e gasato!")
                            elif hittato:
                                st.caption("💥 Ha hittato!")
                        with col2:
                            st.metric("⭐ Media", d["_media"])
