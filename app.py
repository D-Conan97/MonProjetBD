import sqlite3
import streamlit as st
import pandas as pd

# Connexion 
def get_connection():
    return sqlite3.connect("hotel.db", check_same_thread=False)

# Initialisation de la base et des tables
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Client (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_complet TEXT,
            adresse TEXT,
            ville TEXT,
            code_postal INTEGER,
            email TEXT,
            telephone TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Chambre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            type TEXT,
            prix REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_debut TEXT,
            date_fin TEXT,
            id_client INTEGER,
            FOREIGN KEY(id_client) REFERENCES Client(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reservation_Chambre (
            id_reservation INTEGER,
            id_chambre INTEGER,
            PRIMARY KEY (id_reservation, id_chambre),
            FOREIGN KEY(id_reservation) REFERENCES Reservation(id),
            FOREIGN KEY(id_chambre) REFERENCES Chambre(id)
        )
    """)
    
    # Insérer des chambres de test si table vide
    cursor.execute("SELECT COUNT(*) FROM Chambre")
    if cursor.fetchone()[0] == 0:
        chambres_test = [
            ("101", "Simple", 50.0),
            ("102", "Double", 80.0),
            ("201", "Suite", 150.0)
        ]
        cursor.executemany("INSERT INTO Chambre (numero, type, prix) VALUES (?, ?, ?)", chambres_test)
    
    conn.commit()
    conn.close()

# Appel initial pour créer la base
init_db()

# Consultation de tables
def show_table(name):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {name}", conn)
    conn.close()
    st.dataframe(df)

# Ajouter un client
def add_client():
    st.subheader("Ajouter un nouveau client")
    with st.form("form_client"):
        nom = st.text_input("Nom complet")
        adresse = st.text_input("Adresse")
        ville = st.text_input("Ville")
        code_postal = st.number_input("Code postal", step=1)
        email = st.text_input("Email")
        tel = st.text_input("Téléphone")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Client (adresse, ville, code_postal, email, telephone, nom_complet)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (adresse, ville, code_postal, email, tel, nom))
            conn.commit()
            conn.close()
            st.success("Client ajouté avec succès")

# Ajouter une réservation
def add_reservation():
    st.subheader("Ajouter une réservation")
    conn = get_connection()
    clients = pd.read_sql_query("SELECT id, nom_complet FROM Client", conn)
    chambres = pd.read_sql_query("SELECT id, numero FROM Chambre", conn)

    with st.form("form_reservation"):
        client_id = st.selectbox("Client", clients["id"], format_func=lambda i: clients.loc[clients.id==i, "nom_complet"].values[0])
        chambre_id = st.selectbox("Chambre", chambres["id"], format_func=lambda i: chambres.loc[chambres.id==i, "numero"].values[0])
        date_debut = st.date_input("Date début")
        date_fin = st.date_input("Date fin")
        submitted = st.form_submit_button("Réserver")
        if submitted:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Reservation (date_debut, date_fin, id_client) VALUES (?, ?, ?)
            """, (date_debut.isoformat(), date_fin.isoformat(), client_id))
            reservation_id = cursor.lastrowid
            cursor.execute("INSERT INTO Reservation_Chambre VALUES (?, ?)", (reservation_id, chambre_id))
            conn.commit()
            conn.close()
            st.success("Réservation ajoutée avec succès")

# Chambres disponibles
def chambres_disponibles():
    st.subheader("Chambres disponibles pour une période donnée")
    conn = get_connection()
    with st.form("form_disponibilite"):
        date1 = st.date_input("Date de début")
        date2 = st.date_input("Date de fin")
        submitted = st.form_submit_button("Rechercher")
        if submitted:
            query = """
            SELECT * FROM Chambre WHERE id NOT IN (
                SELECT RC.id_chambre
                FROM Reservation R
                JOIN Reservation_Chambre RC ON R.id = RC.id_reservation
                WHERE NOT (R.date_fin < ? OR R.date_debut > ?)
            )
            """
            df = pd.read_sql_query(query, conn, params=(date1.isoformat(), date2.isoformat()))
            st.dataframe(df)
            conn.close()

# Interface principale
st.title("Interface de gestion hôtelière")
choix = st.sidebar.radio("Menu", [
    "Consulter les réservations",
    "Consulter les clients",
    "Consulter les chambres disponibles",
    "Ajouter un client",
    "Ajouter une réservation"
])

if choix == "Consulter les réservations":
    show_table("Reservation")
elif choix == "Consulter les clients":
    show_table("Client")
elif choix == "Consulter les chambres disponibles":
    chambres_disponibles()
elif choix == "Ajouter un client":
    add_client()
elif choix == "Ajouter une réservation":
    add_reservation()
