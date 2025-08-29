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
# Navigation
# -------------------------------
menu = st.sidebar.radio("Navigation", [
    "Ajouter une performance",
    "Voir mes performances",
    "Gérer mes séances",
    "Gestion des utilisateurs"
])

# -------------------------------
# Gestion des utilisateurs
# -------------------------------
if menu == "Gestion des utilisateurs":
    st.header("👥 Gestion des utilisateurs")
    
    users_data = supabase.table("users").select("*").execute()
    if users_data.data:
        df_users = pd.DataFrame(users_data.data)
        if "created_at" in df_users.columns:
            df_users["created_at_local"] = pd.to_datetime(df_users["created_at"]).dt.tz_convert("Europe/Paris")
            st.table(df_users[["name", "created_at_local"]])
        else:
            st.table(df_users[["name"]])
    else:
        st.info("Aucun utilisateur disponible")

    st.subheader("Créer un nouvel utilisateur")
    new_user = st.text_input("Nom du nouvel utilisateur", key="new_user")
    if st.button("Créer utilisateur"):
        existing_names = [u["name"] for u in users_data.data] if users_data.data else []
        if new_user and new_user not in existing_names:
            supabase.table("users").insert({"name": new_user}).execute()
            st.success(f"Utilisateur '{new_user}' créé !")
            st.experimental_rerun()
        else:
            st.error("Nom invalide ou déjà existant")

    if users_data.data:
        users = [u["name"] for u in users_data.data]
        selected_user = st.selectbox("Sélectionner un utilisateur", users, key="select_user")

        new_name = st.text_input("Nouveau nom", value=selected_user, key="rename_user")
        if st.button("Modifier le nom de l'utilisateur"):
            supabase.table("users").update({"name": new_name}).eq("name", selected_user).execute()
            supabase.table("performances").update({"user_id": new_name}).eq("user_id", selected_user).execute()
            st.success(f"Utilisateur '{selected_user}' renommé en '{new_name}'")
            st.experimental_rerun()

        if st.button("Supprimer l'utilisateur"):
            supabase.table("performances").delete().eq("user_id", selected_user).execute()
            supabase.table("users").delete().eq("name", selected_user).execute()
            st.success(f"Utilisateur '{selected_user}' supprimé !")
            st.experimental_rerun()

# -------------------------------
# Ajouter une performance
# -------------------------------
elif menu == "Ajouter une performance":
    st.header("➕ Ajouter une performance")

    # Utilisateur
    users_data = supabase.table("users").select("*").execute()
    users = [u["name"] for u in users_data.data] if users_data.data else []
    user = st.selectbox("Utilisateur", options=users)
    user_id = [u["id"] for u in users_data.data if u["name"] == user][0]

    # Séance
    seances_data = supabase.table("seances").select("*").execute()
    seances = [s["name"] for s in seances_data.data]
    seance_selectionnee = st.selectbox("Séance", options=seances)
    seance_id = [s["id"] for s in seances_data.data if s["name"] == seance_selectionnee][0]

    # Exercice
    exercises_data = supabase.table("exercises").select("*").eq("seance_id", seance_id).execute()
    exercises = [e["name"] for e in exercises_data.data]
    exercises.append("Nouvel exercice")
    exo = st.selectbox("Exercice", options=exercises)
    if exo == "Nouvel exercice":
        exo_input = st.text_input("Nom du nouvel exercice")
        if exo_input:
            supabase.table("exercises").insert({"name": exo_input, "seance_id": seance_id}).execute()
            exo = exo_input

    # Poids
    poids_option = st.radio("Poids", ["Poids du corps", "Avec poids"])
    if poids_option == "Poids du corps":
        poids = 0
    else:
        poids_input = st.text_input("Poids (kg)", "")
        try:
            poids = int(float(poids_input)) if poids_input else 0
        except ValueError:
            st.error("⚠️ Saisis un nombre entier valide pour le poids.")
            poids = 0

    # Séries et répétitions
    nb_series = st.selectbox("Nombre de séries", [1, 2, 3, 4])
    reps_series = [st.number_input(f"Répétitions série {i+1}", min_value=0, step=1, key=f"rep{i}") for i in range(nb_series)]
    notes = st.text_area("Notes (optionnel)")
    d = st.date_input("Date", value=date.today())

    # Enregistrement
    if st.button("Enregistrer"):
        if user and exo and (poids > 0 or poids_option == "Poids du corps") and all(r > 0 for r in reps_series):
            supabase.table("performances").insert({
                "user_id": user_id,
                "seance_id": seance_id,
                "exercice": exo,
                "poids": poids,
                "reps_series": reps_series or [],
                "notes": notes.strip(),
                "date": d.isoformat()
            }).execute()
            st.success("✅ Performance enregistrée !")

    # Tableau des performances du jour
    st.subheader(f"📋 Performances de {user} - {date.today().isoformat()}")
    data = supabase.table("performances").select("*")\
        .eq("user_id", user_id).eq("date", date.today().isoformat())\
        .order("date", desc=True).execute()
    df = pd.DataFrame(data.data)
    if not df.empty:
        df["reps_series"] = df["reps_series"].apply(lambda x: str(x or []))
        df_display = df[["date", "exercice", "poids", "reps_series", "notes"]]
        st.table(df_display)

        options = [f"{row['date']} | {row['exercice']}" for idx, row in df.iterrows()]
        ligne_a_supprimer = st.selectbox("Sélectionne la performance à supprimer", options)
        if st.button("Supprimer la ligne sélectionnée"):
            date_sel, exo_sel = ligne_a_supprimer.split(" | ")
            supabase.table("performances")\
                .delete()\
                .eq("user_id", user_id)\
                .eq("date", date_sel)\
                .eq("exercice", exo_sel)\
                .execute()
            st.success("✅ Performance supprimée !")
            st.experimental_rerun()

# -------------------------------
# Voir mes performances
# -------------------------------
elif menu == "Voir mes performances":
    st.header("📊 Visualiser les performances")

    users_data = supabase.table("users").select("*").execute()
    users = [u["name"] for u in users_data.data]
    user = st.selectbox("Utilisateur", options=users)
    user_id = [u["id"] for u in users_data.data if u["name"] == user][0]

    data = supabase.table("performances").select("*").eq("user_id", user_id).execute()
    df = pd.DataFrame(data.data)

    if df.empty:
        st.warning("Aucune donnée trouvée.")
    else:
        st.subheader("Toutes les performances")
        st.dataframe(df)

        # PR par exercice
        st.subheader("🏆 PR (Poids max) par exercice")
        exercises_data = supabase.table("exercises").select("*").execute()
        df_exercises = pd.DataFrame(exercises_data.data)
        pr_list = []
        for ex in df["exercice"].unique():
            subset = df[df["exercice"] == ex]
            idx_max = subset["poids"].idxmax()
            seance_id = subset.loc[idx_max, "seance_id"]
            seance_name = df_exercises.loc[df_exercises["id"] == seance_id, "name"].values[0] if not df_exercises.empty else "Inconnue"
            pr_row = {
                "exercice": ex,
                "seance": seance_name,
                "poids_max": subset.loc[idx_max, "poids"],
                "date": subset.loc[idx_max, "date"]
            }
            pr_list.append(pr_row)
        df_pr = pd.DataFrame(pr_list)
        st.table(df_pr.sort_values(by="seance"))

        # Graphiques
        st.subheader("Évolution du poids par exercice")
        for ex in df["exercice"].unique():
            subset = df[df["exercice"] == ex]
            st.line_chart(subset, x="date", y="poids", use_container_width=True)

# -------------------------------
# Gérer mes séances
# -------------------------------
elif menu == "Gérer mes séances":
    st.header("📋 Gestion des séances et exercices")

    # Séances
    seances_data = supabase.table("seances").select("*").execute()
    seances = [s["name"] for s in seances_data.data]
    seance_selectionnee = st.selectbox("Sélectionner une séance", options=seances)
    seance_id = [s["id"] for s in seances_data.data if s["name"] == seance_selectionnee][0]

    # Modifier le nom
    new_name = st.text_input("Nouveau nom de la séance", value=seance_selectionnee)
    if st.button("Modifier le nom de la séance"):
        supabase.table("seances").update({"name": new_name}).eq("id", seance_id).execute()
        st.success("Nom de la séance modifié !")
        st.experimental_rerun()

    # Exercices
    exercises_data = supabase.table("exercises").select("*").eq("seance_id", seance_id).execute()
    if exercises_data.data:
        df_exos = pd.DataFrame(exercises_data.data)
        st.subheader("📋 Exercices de la séance")
        st.table(df_exos[["name"]])
    else:
        st.info("Aucun exercice pour cette séance")

    st.subheader("Ajouter un nouvel exercice")
    new_exo = st.text_input("Nom de l'exercice")
    if st.button("Ajouter l'exercice"):
        if new_exo and new_exo not in [e["name"] for e in exercises_data.data]:
            supabase.table("exercises").insert({"name": new_exo, "seance_id": seance_id}).execute()
            st.success("Exercice ajouté !")
            st.experimental_rerun()

    st.subheader("Supprimer un exercice")
    if exercises_data.data:
        exo_sup = st.selectbox("Sélectionner un exercice à supprimer", [e["name"] for e in exercises_data.data])
        if st.button("Supprimer l'exercice"):
            supabase.table("exercises").delete().eq("seance_id", seance_id).eq("name", exo_sup).execute()
            st.success("Exercice supprimé !")
            st.experimental_rerun()

