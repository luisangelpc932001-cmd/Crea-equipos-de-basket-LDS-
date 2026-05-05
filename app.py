import streamlit as st
import pandas as pd
import random

# =========================
# CONFIGURACIÓN
# =========================
ARCHIVO = "Jugadores 1.csv"

ATRIBUTOS = [
    "Altura",
    "Velocidad",
    "Habilidad",
    "Tiro Interior",
    "Tiro Exterior"
]

LIMITE = 20

# =========================
# CARGA DE JUGADORES (SIMPLE Y FIJA)
# =========================
@st.cache_data
def cargar_jugadores():
    df = pd.read_csv(
        ARCHIVO,
        sep=";",            # CSV de Excel en español
        encoding="latin-1"  # acentos
    )
    return df

# =========================
# CREAR EQUIPOS
# =========================
def crear_equipos(df, seleccionados):
    jugadores = df[df["Jugador"].isin(seleccionados)].to_dict("records")
    random.shuffle(jugadores)

    num_equipos = len(jugadores) // 5
    equipos = [[] for _ in range(num_equipos)]
    stats = [{a: 0 for a in ATRIBUTOS} for _ in range(num_equipos)]

    def puede_entrar(j, s):
        return all(s[a] + j[a] <= LIMITE for a in ATRIBUTOS)

    for jugador in jugadores:
        for i in range(num_equipos):
            if len(equipos[i]) < 5 and puede_entrar(jugador, stats[i]):
                equipos[i].append(jugador)
                for a in ATRIBUTOS:
                    stats[i][a] += jugador[a]
                break

    asignados = [j for e in equipos for j in e]
    sobrantes = [j for j in jugadores if j not in asignados]

    return equipos, sobrantes

# =========================
# INTERFAZ
# =========================
st.title("🏀 Generador de Equipos de Basket")

df = cargar_jugadores()

jugadores_seleccionados = st.multiselect(
    "Selecciona quiénes están hoy:",
    df["Jugador"].tolist()
)

if st.button("🔥 Crear equipos"):
    if len(jugadores_seleccionados) < 5:
        st.warning("Selecciona al menos 5 jugadores.")
    else:
        equipos, sobrantes = crear_equipos(df, jugadores_seleccionados)

        for i, equipo in enumerate(equipos, 1):
            st.subheader(f"🏀 Equipo {i}")
            totales = {a: 0 for a in ATRIBUTOS}

            for j in equipo:
                st.write(
                    f"{j['Jugador']} "
                    f"(A:{j['Altura']} V:{j['Velocidad']} H:{j['Habilidad']} "
                    f"TI:{j['Tiro Interior']} TE:{j['Tiro Exterior']})"
                )
                for a in ATRIBUTOS:
                    totales[a] += j[a]

            st.write("Totales:", totales)

        if sobrantes:
            st.subheader("🟡 Sobrantes")
            for j in sobrantes:
                st.write(j["Jugador"])