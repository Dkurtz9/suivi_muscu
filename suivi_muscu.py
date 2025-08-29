import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# -------------------------------
# Connexion à Supabase
# -------------------------------
url = "https://bkufxjnztblopmgevjjn.supabase.co"  # Remplacer par ton URL
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrdWZ4am56dGJsb3BtZ2V2ampuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY0NTk0NjMsImV4cCI6MjA3MjAzNTQ2M30.B9v80nW61NOMp4mWF_IFzVZelRBxOm463jvKoNFDl0U"  # Remplacer par ta clé anon
supabase = create_client(url, key)

# -------------------------------
# Interface utilisateur Streamlit
# -------------------------------
st.set_page_config(page_title="Suivi Muscu", layout="centered")
st.title("🏋️ Suivi Musculation")

# Récupérer la liste des utilisateurs existants
users_data = supabase.table("performances").select("user_id").execute()
users = sorted(list({row["user_id"] for row in users_data.data}))  # unique + tri

menu = st.sidebar.radio("Navigation", ["Ajouter une performance", "Voir mes performances"])

# -------------------------------
# Ajouter une performance
# -------------------------------
if menu == "Ajouter une performance":
    st.header("➕ Ajouter une performance")

    # Menu déroulant utilisateur
    user = st.selectbox("Utilisateur", options=users if users else ["nouvel utilisateur"])
    if user == "nouvel utilisateur":
        user = st.text_input("Nom du nouvel utilisateur")

    # Récupérer la liste des exercices existants
    exercises_data = supabase.table("exercises").select("name").execute()
    exercises = sorted([row["name"] for row in exercises_data.data])
    exercises.append("Nouvel exercice")  # option pour en créer un nouveau

    # Menu déroulant exercices
    exo = st.selectbox("Exercice", options=exercises)
    if exo == "Nouvel exercice":
        exo = st.text_input("Nom du nouvel exercice")

    poids = st.number_input("Poids (kg)", min_value=0.0, step=0.5)
    reps = st.number_input("Répétitions", min_value=0, step=1)
    series = st.number_input("Nombre de séries", min_value=1, step=1)
    notes = st.text_area("Notes (optionnel)")
    d = st.date_input("Date", value=date.today())

    if st.button("Enregistrer"):
        if user and exo and poids > 0 and reps > 0 and series > 0:
            # Ajouter l'exercice à la table exercises si c'est un nouvel exercice
            if exercises_data.data == [] or exo not in exercises:
                supabase.table("exercises").insert({"name": exo}).execute()

            # Ajouter la performance
            supabase.table("performances").insert({
                "user_id": user,
                "date": d.isoformat(),
                "exercice": exo.strip(),
                "poids": poids,
                "reps": reps,
                "series": series,
                "notes": notes.strip()
            }).execute()
            st.success("✅ Performance enregistrée !")
        else:
            st.error("⚠️ Remplis tous les champs obligatoires.")

# -------------------------------
# Visualiser les performances
# -------------------------------
if menu == "Voir mes performances":
    st.header("📊 Mes performances")

    # Menu déroulant utilisateur
    user = st.selectbox("Utilisateur", options=users)

    if user:
        data = supabase.table("performances").select("*").eq("user_id", user).order("date", desc=True).execute()
        df = pd.DataFrame(data.data)

        if df.empty:
            st.warning("Aucune donnée trouvée.")
        else:
            st.dataframe(df)

            # Graphique évolution poids par exercice
            st.subheader("Évolution du poids par exercice")
            exos = df["exercice"].unique()
            for ex in exos:
                subset = df[df["exercice"] == ex]
                st.line_chart(subset, x="date", y="poids", use_container_width=True)
