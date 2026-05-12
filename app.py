import streamlit as st
import pandas as pd
import random
import unicodedata
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
SHEET_ID = "1_On2uHmWkPu_cPNyomeS2thZuf7r9TH1SbG1uuMliTU"
SHEET_NAME = "Hoja 1"  # Cambia esto si tu hoja tiene otro nombre

ATRIBUTOS = ["Altura", "Velocidad", "Habilidad", "Tiro Interior", "Tiro Exterior"]
LIMITE = 20

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# =========================
# CONEXIÓN A GOOGLE SHEETS
# =========================
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    return sheet


# =========================
# NORMALIZAR TEXTO
# =========================
def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')


# =========================
# CARGAR DATOS
# =========================
@st.cache_data(ttl=60)
def cargar_jugadores():
    sheet = get_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = ["Jugador"] + ATRIBUTOS
    df["Jugador_norm"] = df["Jugador"].apply(normalizar)
    return df


# =========================
# GUARDAR NUEVO JUGADOR
# =========================
def guardar_jugador(jugador):
    sheet = get_sheet()
    fila = [jugador["Jugador"]] + [jugador[attr] for attr in ATRIBUTOS]
    sheet.append_row(fila)
    st.cache_data.clear()


# =========================
# CREAR EQUIPOS
# =========================
def crear_equipos(df, jugadores_presentes):
    df_hoy = df[df["Jugador"].isin(jugadores_presentes)].copy()
    jugadores = df_hoy.to_dict("records")

    num_equipos = len(jugadores) // 5

    equipos = [[] for _ in range(num_equipos)]
    stats = [{attr: 0 for attr in ATRIBUTOS} for _ in range(num_equipos)]

    def balance(stats):
        score = 0
        for attr in ATRIBUTOS:
            valores = [s[attr] for s in stats]
            score += max(valores) - min(valores)
        return score

    def puede_agregar(jugador, equipo, stats_equipo):
        for attr in ATRIBUTOS:
            if stats_equipo[attr] + jugador[attr] > LIMITE:
                return False
            valores = [j[attr] for j in equipo]
            if jugador[attr] == 5 and 5 in valores:
                return False

        alturas = [j["Altura"] for j in equipo]
        if jugador["Altura"] == 5 and alturas.count(5) >= 1:
            return False
        if jugador["Altura"] == 4 and alturas.count(4) >= 2:
            return False

        return True

    random.shuffle(jugadores)

    for jugador in jugadores:
        mejor = None
        mejor_score = float("inf")

        for i in range(num_equipos):
            if len(equipos[i]) >= 5:
                continue
            if not puede_agregar(jugador, equipos[i], stats[i]):
                continue

            temp = [s.copy() for s in stats]
            for attr in ATRIBUTOS:
                temp[i][attr] += jugador[attr]

            score = balance(temp)
            if score < mejor_score:
                mejor_score = score
                mejor = i

        if mejor is not None:
            equipos[mejor].append(jugador)
            for attr in ATRIBUTOS:
                stats[mejor][attr] += jugador[attr]

    asignados = [j for equipo in equipos for j in equipo]
    sobrantes = [j for j in jugadores if j not in asignados]

    return equipos, sobrantes


# =========================
# UI
# =========================
st.title("🏀 Generador de Equipos de Basket")

df = cargar_jugadores()

jugadores_seleccionados = st.multiselect(
    "Selecciona quiénes están hoy:",
    df["Jugador"].tolist()
)

if st.button("🔥 Crear equipos"):
    if len(jugadores_seleccionados) < 5:
        st.warning("Necesitas al menos 5 jugadores")
    else:
        equipos, sobrantes = crear_equipos(df, jugadores_seleccionados)

        for i, equipo in enumerate(equipos, 1):
            st.subheader(f"🏀 Equipo {i}")
            totales = {attr: 0 for attr in ATRIBUTOS}

            for j in equipo:
                st.write(
                    f"{j['Jugador']} "
                    f"(A:{j['Altura']} V:{j['Velocidad']} "
                    f"H:{j['Habilidad']} TI:{j['Tiro Interior']} TE:{j['Tiro Exterior']})"
                )
                for attr in ATRIBUTOS:
                    totales[attr] += j[attr]

            st.write("👉 Totales:", totales)

        if sobrantes:
            st.subheader("🟡 Equipo a completar")
            for j in sobrantes:
                st.write(
                    f"{j['Jugador']} "
                    f"(A:{j['Altura']} V:{j['Velocidad']} "
                    f"H:{j['Habilidad']} TI:{j['Tiro Interior']} TE:{j['Tiro Exterior']})"
                )


# =========================
# AÑADIR JUGADOR
# =========================
st.divider()
st.subheader("➕ Añadir jugador nuevo")

with st.form("nuevo_jugador"):
    nombre = st.text_input("Nombre")
    valores = {attr: st.slider(attr, 1, 5, 3) for attr in ATRIBUTOS}

    if st.form_submit_button("Guardar jugador"):
        if nombre.strip() == "":
            st.warning("Escribe un nombre para el jugador")
        else:
            nuevo = {"Jugador": nombre}
            nuevo.update(valores)
            guardar_jugador(nuevo)
            st.success(f"✅ {nombre} añadido correctamente")
