import streamlit as st
import pandas as pd
import random

# =========================
# CONFIG
# =========================
ARCHIVO = "Jugadores 1.csv"

ATRIBUTOS = ["Altura", "Velocidad", "Habilidad", "Tiro Interior", "Tiro Exterior"]
LIMITE = 20

# =========================
# CARGAR JUGADORES (SIMPLE Y CORRECTO)
# =========================
@st.cache_data
def cargar_jugadores():
    df = pd.read_csv(
        ARCHIVO,
        sep=";",            # ✅ separador correcto (Excel español)
        encoding="latin-1"  # ✅ acentos y ñ
    )

    # comprobación clara
    if df.shape[1] != 6:
        st.error(
            f"❌ El CSV debe tener 6 columnas.\n"
            f"Se encontraron {df.shape[1]}.\n"
            f"Revisa que el separador sea ';'."
        )
        st.stop()

    return df

# =========================
# CREAR EQUIPOS
# =========================
def crear_equipos(df, jugadores_presentes):

    jugadores = df[df["Jugador"].isin(jugadores_presentes)].to_dict("records")
    num_equipos = len(jugadores) // 5

    equipos = [[] for _ in range(num_equipos)]
    stats = [{a: 0 for a in ATRIBUTOS} for _ in range(num_equipos)]

    def puede_agregar(jugador, equipo, stats_equipo):
        for a in ATRIBUTOS:
            if stats_equipo[a] + jugador[a] > LIMITE:
                return False
        return True

    random.shuffle(jugadores)

    for jugador in jugadores:
        for i in range(num_equipos):
            if len(equipos[i]) < 5 and puede_agregar(jugador, equipos[i], stats[i]):
                equipos[i].append(jugador)
                for a in ATRIBUTOS:
                    stats[i][a] += jugador[a]
                break

    asignados = [j for e in equipos for j in e]
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
    equipos, sobrantes = crear_equipos(df, jugadores_seleccionados)

    for i, equipo in enumerate(equipos, 1):
        st.subheader(f"🏀 Equipo {i}")
        for j in equipo:
            st.write(
                f"{j['Jugador']} "
                f"(A:{j['Altura']} V:{j['Velocidad']} "
                f"H:{j['Habilidad']} TI:{j['Tiro Interior']} TE:{j['Tiro Exterior']})"
            )

    if sobrantes:
        st.subheader("🟡 Equipo a completar")
        for j in sobrantes:
            st.write(j["Jugador"])
