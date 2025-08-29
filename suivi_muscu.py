import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# -------------------------------
# Connexion à Supabase
# -------------------------------
url = "https://bkufxjnztblopmgevjjn.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrdWZ4am56dGJsb3BtZ2V2ampuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY0NTk0NjMsImV4cCI6MjA3MjAzNTQ2M30.B9v80nW61NOMp4mWF_IFzVZelRBxOm463jvKoNFDl0U"
supabase = create_client(url, key)

# -------------------------------
# Interface utilisateur
# -------------------------------
st.set_page_config(page_title="Suivi Muscu", layout="centered")
st.title("🏋️ Suivi Musculation")

# Récupérer les utilisateurs
users_data = supabase.table("performances").select("user_id").execute()
users = sorted(list({row["user_id"] for row in users_data.data}))

menu = st.sidebar.radio("Navigation", ["Ajouter une performance", "Voir mes performances", "Gérer les séances"])

# -------------------------------
# Ajouter une performance
# -------------------------------
if menu == "Ajouter une performance":
    st.header("➕ Ajouter une performance")

    # ----- Sélection de l'utilisateur -----
    users_data = supabase.table("performances").select("user_id").execute()
    users = sorted(list({row["user_id"] for row in users_data.data}))
    user = st.selectbox("Utilisateur", options=users if users else ["Nouvel utilisateur"])
    if user == "Nouvel utilisateur":
        user = st.text_input("Nom du nouvel utilisateur")

    # ----- Sélection de la séance et de l'exercice -----
    seances_data = supabase.table("seances").select("*").execute()
    seances = [s["name"] for s in seances_data.data]
    seance_selectionnee = st.selectbox("Séance", options=seances)

    seance_id = [s["id"] for s in seances_data.data if s["name"] == seance_selectionnee][0]
    exercises_data = supabase.table("exercises").select("*").eq("seance_id", seance_id).execute()
    exercises = [e["name"] for e in exercises_data.data]
    exercises.append("Nouvel exercice")
    exo = st.selectbox("Exercice", options=exercises)
    if exo == "Nouvel exercice":
        exo = st.text_input("Nom du nouvel exercice")
        if exo:
            supabase.table("exercises").insert({"name": exo, "seance_id": seance_id}).execute()

    # ----- Performance -----
    poids_input = st.text_input("Poids (kg)", "")
try:
    poids = float(poids_input) if poids_input else 0.0
except ValueError:
    st.error("⚠️ Saisis un nombre valide pour le poids.")
    poids = 0.0
    nb_series = st.selectbox("Nombre de séries", [1, 2, 3, 4])
    reps_series = [st.number_input(f"Répétitions série {i+1}", min_value=0, step=1, key=f"rep{i}") for i in range(nb_series)]
    notes = st.text_area("Notes (optionnel)")
    d = st.date_input("Date", value=date.today())

    # ----- Enregistrer la performance -----
    if st.button("Enregistrer"):
        if user and exo and poids > 0 and all(r > 0 for r in reps_series):
            supabase.table("performances").insert({
                "user_id": user,
                "date": d.isoformat(),
                "exercice": exo,
                "poids": poids,
                "reps_series": reps_series or [],
                "notes": notes.strip()
            }).execute()
            st.success("✅ Performance enregistrée !")

    # ----- Visualiser toutes les performances sous forme de tableau avec suppression -----
    st.subheader(f"📋 Performances de {user}")
    data = supabase.table("performances").select("*").eq("user_id", user).order("date", desc=True).execute()
    df = pd.DataFrame(data.data)

    if not df.empty:
        df["reps_series"] = df["reps_series"].apply(lambda x: x or [])

        # Affichage du libellé des colonnes
        cols = st.columns([2, 2, 1, 1, 2, 1])
        cols[0].write("Date")
        cols[1].write("Exercice")
        cols[2].write("Poids (kg)")
        cols[3].write("Répétitions")
        cols[4].write("Notes")
        cols[5].write("Actions")

        # Affichage ligne par ligne
        for idx, row in df.iterrows():
            cols = st.columns([2, 2, 1, 1, 2, 1])
            cols[0].write(row["date"])
            cols[1].write(row["exercice"])
            cols[2].write(row["poids"])
            cols[3].write(str(row["reps_series"]))
            cols[4].write(row["notes"])

            # Bouton Supprimer
            if cols[5].button("Supprimer", key=f"del_{row['id']}"):
                supabase.table("performances").delete().eq("id", row["id"]).execute()
                st.success("✅ Performance supprimée !")
                st.experimental_rerun()


# -------------------------------
# Visualiser les performances
# -------------------------------
if menu == "Voir mes performances":
    st.header("📊 Mes performances")
    user = st.selectbox("Utilisateur", options=users)
    if user:
        data = supabase.table("performances").select("*").eq("user_id", user).order("date", desc=True).execute()
        df = pd.DataFrame(data.data)
        if df.empty:
            st.warning("Aucune donnée trouvée.")
        else:
            st.dataframe(df)
            st.subheader("Évolution du poids par exercice")
            exos = df["exercice"].unique()
            for ex in exos:
                subset = df[df["exercice"] == ex]
                st.line_chart(subset, x="date", y="poids", use_container_width=True)

# -------------------------------
# Gérer les séances
# -------------------------------
if menu == "Gérer les séances":
    st.header("🗂️ Gestion des séances")

    # ----- Créer une nouvelle séance -----
    st.subheader("➕ Créer une nouvelle séance")
    nouvelle_seance = st.text_input("Nom de la séance")
    if st.button("Créer la séance"):
        if nouvelle_seance:
            existing = supabase.table("seances").select("*").eq("name", nouvelle_seance).execute()
            if existing.data:
                st.warning("Cette séance existe déjà.")
            else:
                supabase.table("seances").insert({"name": nouvelle_seance}).execute()
                st.success(f"✅ Séance '{nouvelle_seance}' créée !")
                st.experimental_rerun = lambda: None  # ne fait rien et évite l'erreur

    # ----- Modifier le nom d'une séance -----
    st.subheader("✏️ Modifier le nom d'une séance existante")
    seances_data = supabase.table("seances").select("*").execute()
    seances = [s["name"] for s in seances_data.data]
    if seances:
        seance_a_modifier = st.selectbox("Sélectionner une séance à modifier", options=seances)
        nouveau_nom = st.text_input("Nouveau nom de la séance")
        if st.button("Modifier le nom"):
            if nouveau_nom:
                existing = supabase.table("seances").select("*").eq("name", nouveau_nom).execute()
                if existing.data:
                    st.warning("Une séance avec ce nom existe déjà.")
                else:
                    seance_id = [s["id"] for s in seances_data.data if s["name"] == seance_a_modifier][0]
                    supabase.table("seances").update({"name": nouveau_nom}).eq("id", seance_id).execute()
                    st.success(f"✅ La séance '{seance_a_modifier}' a été renommée en '{nouveau_nom}' !")
                    st.experimental_rerun = lambda: None  # ne fait rien et évite l'erreur

    # ----- Ajouter des exercices à une séance existante -----
    st.subheader("➕ Ajouter des exercices à une séance existante")
    if seances:
        seance_selectionnee = st.selectbox("Sélectionner une séance", options=seances, key="seance_exo")

        nouveau_exo = st.text_input("Nom du nouvel exercice à ajouter")
        if st.button("Ajouter l'exercice"):
            if seance_selectionnee and nouveau_exo:
                seance_id = [s["id"] for s in seances_data.data if s["name"] == seance_selectionnee][0]
                existing_exo = supabase.table("exercises").select("*").eq("name", nouveau_exo).eq("seance_id", seance_id).execute()
                if existing_exo.data:
                    st.warning("Cet exercice existe déjà dans cette séance.")
                else:
                    supabase.table("exercises").insert({"name": nouveau_exo, "seance_id": seance_id}).execute()
                    st.success(f"✅ Exercice '{nouveau_exo}' ajouté à la séance '{seance_selectionnee}' !")
                    st.experimental_rerun = lambda: None  # ne fait rien et évite l'erreur

        # ----- Visualiser et supprimer les exercices -----
        st.subheader(f"📋 Exercices dans la séance '{seance_selectionnee}'")
        seance_id = [s["id"] for s in seances_data.data if s["name"] == seance_selectionnee][0]
        exercises_data = supabase.table("exercises").select("*").eq("seance_id", seance_id).execute()
        exercises = exercises_data.data

        if exercises:
            for ex in exercises:
                col1, col2 = st.columns([4, 1])
                col1.write(f"- {ex['name']}")
                if col2.button("Supprimer", key=f"del_{ex['id']}"):
                    supabase.table("exercises").delete().eq("id", ex["id"]).execute()
                    st.success(f"Exercice '{ex['name']}' supprimé !")
                    st.experimental_rerun = lambda: None  # ne fait rien et évite l'erreur
        else:
            st.info("Aucun exercice dans cette séance.")

