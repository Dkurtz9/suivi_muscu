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

    # Utilisateur
    user = st.selectbox("Utilisateur", options=users if users else ["nouvel utilisateur"])
    if user == "nouvel utilisateur":
        user = st.text_input("Nom du nouvel utilisateur")

    # Séance
    seances_data = supabase.table("seances").select("*").execute()
    seances = [row["name"] for row in seances_data.data]
    seances.append("Nouvelle séance")
    seance = st.selectbox("Séance", options=seances)
    if seance == "Nouvelle séance":
        seance = st.text_input("Nom de la nouvelle séance")
        # Ajouter la séance si remplie
        if seance:
            supabase.table("seances").insert({"name": seance}).execute()

    # Exercices associés à la séance
    exercises_data = supabase.table("exercises").select("*").execute()
    exercises = [row["name"] for row in exercises_data.data if row["seance_id"] in [s["id"] for s in seances_data.data if s["name"]==seance]]
    exercises.append("Nouvel exercice")
    exo = st.selectbox("Exercice", options=exercises)
    if exo == "Nouvel exercice":
        exo = st.text_input("Nom du nouvel exercice")
        # Ajouter l'exercice à la séance
        if exo:
            seance_id = [s["id"] for s in seances_data.data if s["name"]==seance][0]
            supabase.table("exercises").insert({"name": exo, "seance_id": seance_id}).execute()

    poids = st.number_input("Poids (kg)", min_value=0.0, step=0.5)

    # Nombre de séries
    nb_series = st.selectbox("Nombre de séries", [1,2,3,4])
    reps_series = []
    for i in range(nb_series):
        reps = st.number_input(f"Répétitions série {i+1}", min_value=0, step=1, key=f"rep{i}")
        reps_series.append(reps)

    notes = st.text_area("Notes (optionnel)")
    d = st.date_input("Date", value=date.today())

    if st.button("Enregistrer"):
        if user and exo and poids > 0 and all(r>0 for r in reps_series):
            supabase.table("performances").insert({
                "user_id": user,
                "date": d.isoformat(),
                "exercice": exo,
                "poids": poids,
                "reps_series": reps_series,
                "notes": notes.strip()
            }).execute()
            st.success("✅ Performance enregistrée !")

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
    st.write("Créer ou modifier des séances et leurs exercices depuis ici.")


