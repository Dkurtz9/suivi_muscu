import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client
import os

# -------------------------------
# Connexion à Supabase
# -------------------------------
url = "https://bkufxjnztblopmgevjjn.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrdWZ4am56dGJsb3BtZ2V2ampuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY0NTk0NjMsImV4cCI6MjA3MjAzNTQ2M30.B9v80nW61NOMp4mWF_IFzVZelRBxOm463jvKoNFDl0U"
supabase = create_client(url, key)

# -------------------------------
# Interface utilisateur Streamlit
# -------------------------------
st.set_page_config(page_title="Suivi Muscu", layout="centered")
st.title("🏋️ Suivi Musculation")

menu = st.sidebar.radio("Navigation", ["Ajouter une performance", "Voir mes performances", "Gérer mes séances", "Gestion des utilisateurs"])

# -------------------------------
# Ajouter une performance
# -------------------------------
if menu == "Ajouter une performance":
    st.header("➕ Ajouter une performance")

    # Sélection utilisateur
    users_data = supabase.table("users").select("*").execute()
    users = [u["name"] for u in users_data.data] if users_data.data else []
    user = st.selectbox("Utilisateur", options=users)
    user_id = [u["id"] for u in users_data.data if u["name"] == user][0] if users else None

    # Sélection séance
    seances_data = supabase.table("seances").select("*").execute()
    seances = [s["name"] for s in seances_data.data] if seances_data.data else []
    seance_selectionnee = st.selectbox("Sélectionner une séance", options=seances)
    seance_id = [s["id"] for s in seances_data.data if s["name"] == seance_selectionnee][0] if seances else None

    # Sélection exercice
    exercises_data = supabase.table("exercises").select("*").eq("seance_id", seance_id).execute() if seance_id else None
    exercises = [e["name"] for e in exercises_data.data] if exercises_data and exercises_data.data else []
    exo = st.selectbox("Exercice", options=exercises)

    # Affichage image de l'exercice
    selected_exo_data = next((e for e in exercises_data.data if e["name"] == exo), None) if exercises_data else None
    if selected_exo_data and selected_exo_data.get("image_url"):
        st.image(selected_exo_data["image_url"], use_container_width=True)

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
    nombre_series = st.selectbox("Nombre de séries", options=[1,2,3,4])
    reps_series = []
    for i in range(nombre_series):
        reps = st.number_input(f"Répétitions série {i+1}", min_value=0, step=1)
        reps_series.append(reps)

    notes = st.text_area("Notes (optionnel)")
    d = st.date_input("Date", value=date.today())

    # Bouton enregistrer
    if st.button("Enregistrer"):
        if user and exo and (poids > 0 or poids_option == "Poids du corps") and all(r > 0 for r in reps_series):
            supabase.table("performances").insert({
                "user_id": user_id,
                "seance_id": seance_id,
                "seance_name": seance_selectionnee,
                "exercice": exo,
                "poids": poids,
                "reps_series": reps_series,
                "notes": notes.strip(),
                "date": d.isoformat()
            }).execute()
            st.success("✅ Performance enregistrée !")
        else:
            st.error("⚠️ Remplis tous les champs obligatoires.")

    # Affichage des performances du jour
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
    users = [u["name"] for u in users_data.data] if users_data.data else []
    if not users:
        st.warning("Aucun utilisateur disponible")
    else:
        user = st.selectbox("Utilisateur", options=users)
        user_id = [u["id"] for u in users_data.data if u["name"] == user][0]

        data = supabase.table("performances").select("*").eq("user_id", user_id).execute()
        df = pd.DataFrame(data.data)
        if df.empty:
            st.warning("Aucune performance trouvée pour cet utilisateur.")
        else:
            if "seance_name" not in df.columns:
                df["seance_name"] = "Inconnue"
            df["reps_series"] = df["reps_series"].apply(lambda x: str(x or []))

            st.subheader("📋 Toutes les performances")
            st.dataframe(df[["date","seance_name","exercice","poids","reps_series","notes"]])

            # PR par exercice
            st.subheader("🏆 PR (Poids max) par exercice")
            pr_list = []
            for ex in df["exercice"].unique():
                subset = df[df["exercice"] == ex]
                if not subset.empty:
                    idx_max = subset["poids"].idxmax()
                    seance_name = subset.loc[idx_max, "seance_name"]
                    pr_row = {
                        "exercice": ex,
                        "seance": seance_name,
                        "poids_max": subset.loc[idx_max, "poids"],
                        "date": subset.loc[idx_max, "date"]
                    }
                    pr_list.append(pr_row)
            df_pr = pd.DataFrame(pr_list)
            if not df_pr.empty:
                st.table(df_pr.sort_values(by="seance"))
            else:
                st.info("Aucun PR disponible.")

            # Graphique avec choix d'exercice
            st.subheader("📈 Évolution du poids par exercice")
            exos = df["exercice"].unique()
            exo_selection = st.selectbox("Choisir l'exercice", options=exos)
            subset = df[df["exercice"] == exo_selection]
            if not subset.empty:
                st.line_chart(subset, x="date", y="poids", use_container_width=True)


# -------------------------------
# Gérer mes séances
# -------------------------------
elif menu == "Gérer mes séances":
    st.header("📋 Gestion des séances et exercices")
    seances_data = supabase.table("seances").select("*").execute()
    seances = [s["name"] for s in seances_data.data] if seances_data.data else []
    seance_selectionnee = st.selectbox("Sélectionner une séance", options=seances)
    seance_id = [s["id"] for s in seances_data.data if s["name"]==seance_selectionnee][0] if seances else None

    # Modifier le nom
    new_name = st.text_input("Nouveau nom de la séance", value=seance_selectionnee)
    if st.button("Modifier le nom"):
        if new_name and seance_id:
            supabase.table("seances").update({"name": new_name}).eq("id", seance_id).execute()
            st.success("Nom modifié !")
            st.experimental_rerun()

    # Exercices
    exercises_data = supabase.table("exercises").select("*").eq("seance_id", seance_id).execute() if seance_id else None
    st.subheader("📋 Exercices de la séance")
    if exercises_data and exercises_data.data:
        df_exos = pd.DataFrame(exercises_data.data)
        st.table(df_exos[["name", "image_url"]] if "image_url" in df_exos.columns else df_exos[["name"]])

        # Afficher images
        for ex in exercises_data.data:
            if ex.get("image_url"):
                st.text(f"Exercice : {ex['name']}")
                st.image(ex["image_url"], use_container_width=True)
    else:
        st.info("Aucun exercice pour cette séance")

    # Ajouter un nouvel exercice avec image
    st.subheader("Ajouter un nouvel exercice")
    new_exo = st.text_input("Nom de l'exercice")
    uploaded_file = st.file_uploader("Téléverser une image (png/jpg/jpeg)", type=["png","jpg","jpeg"])
    if st.button("Ajouter l'exercice"):
        if new_exo and seance_id:
            image_url = None
            if uploaded_file:
                os.makedirs("images", exist_ok=True)
                path = f"images/{uploaded_file.name}"
                with open(path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                image_url = path
            supabase.table("exercises").insert({
                "name": new_exo,
                "seance_id": seance_id,
                "image_url": image_url
            }).execute()
            st.success("Exercice ajouté !")
            st.experimental_rerun()

    # Supprimer un exercice
    st.subheader("Supprimer un exercice")
    if exercises_data and exercises_data.data:
        exo_sup = st.selectbox("Sélectionner un exercice à supprimer", [e["name"] for e in exercises_data.data])
        if st.button("Supprimer l'exercice"):
            supabase.table("exercises").delete().eq("seance_id", seance_id).eq("name", exo_sup).execute()
            st.success("Exercice supprimé !")
            st.experimental_rerun()


# -------------------------------
# Gestion des utilisateurs
# -------------------------------
elif menu == "Gestion des utilisateurs":
    st.header("👤 Gestion des utilisateurs")
    users_data = supabase.table("users").select("*").execute()
    df_users = pd.DataFrame(users_data.data) if users_data.data else pd.DataFrame()
    df_users["created_at"] = pd.to_datetime(df_users["created_at"], errors='coerce')
    st.subheader("Liste des utilisateurs")
    if not df_users.empty:
        st.table(df_users[["name","created_at"]])
    else:
        st.info("Aucun utilisateur")

    st.subheader("Ajouter un utilisateur")
    new_user = st.text_input("Nom du nouvel utilisateur")
    if st.button("Ajouter l'utilisateur") and new_user:
        supabase.table("users").insert({"name": new_user}).execute()
        st.success("Utilisateur ajouté !")
        st.experimental_rerun()

    st.subheader("Supprimer un utilisateur")
    if not df_users.empty:
        user_sup = st.selectbox("Sélectionner un utilisateur", df_users["name"].tolist())
        if st.button("Supprimer l'utilisateur"):
            supabase.table("users").delete().eq("name", user_sup).execute()
            st.success("Utilisateur supprimé !")
            st.experimental_rerun()
