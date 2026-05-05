import streamlit as st
import pandas as pd
import random
import unicodedata

# =========================
# CONFIG
# =========================
ARCHIVO = "Jugadores.csv"

ATRIBUTOS = ["Altura", "Velocidad", "Habilidad", "Tiro Interior", "Tiro Exterior"]
LIMITE = 20  # máximo por habilidad

# =========================
# NORMALIZAR TEXTO
# =========================
def normalizar(texto):
    texto = str(texto).lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

# =========================
# CARGAR DATOS (CSV)
# =========================
@st.cache_data
def cargar_jugadores():
    df = pd.read_csv(ARCHIVO)
    df.columns = ["Jugador"] + ATRIBUTOS
    df["Jugador_norm"] = df["Jugador"].apply(normalizar)
    return df

# =========================
# GUARDAR NUEVO JUGADOR (CSV)
# =========================
def guardar_jugador(jugador):
    df = pd.read_csv(ARCHIVO)
    df.columns = ["Jugador"] + ATRIBUTOS
    df = pd.concat([df, pd.DataFrame([jugador])], ignore_index=True)
    df.to_csv(ARCHIVO, index=False)

# =========================
# CREAR EQUIPOS
# =========================
def crear_equipos(df, jugadores_presentes):

    df_hoy = df[df["Jugador"].isin(jugadores_presentes)].copy()
    jugadores = df_hoy.to_dict("records")

    num_equipos = len(jugadores) // 5

    equipos = [[] for _ in range(num_equipos)]
    stats = [{a: 0 for a in ATRIBUTOS} for _ in range(num_equipos)]

    def balance(stats):
        score = 0
        for a in ATRIBUTOS:
            vals = [s[a] for s in stats]
            score += max(vals) - min(vals)
        return score

    def puede_agregar(jugador, equipo, stats_equipo):

        for a in ATRIBUTOS:
            if stats_equipo[a] + jugador[a] > LIMITE:
                return False

            valores = [j[a] for j in equipo]
            if jugador[a] == 5 and 5 in valores:
                return False

        # Reglas especiales de altura
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
            for a in ATRIBUTOS:
                temp[i][a] += jugador[a]

            score = balance(temp)
            if score < mejor_score:
                mejor_score = score
                mejor = i

        if mejor is not None:
            equipos[mejor].append(jugador)
            for a in ATRIBUTOS:
                stats[mejor][a] += jugador[a]

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

    if len(jugadores_seleccionados) < 5:
        st.warning("Necesitas al menos 5 jugadores")
    else:
        equipos, sobrantes = crear_equipos(df, jugadores_seleccionados)

        for i, equipo in enumerate(equipos, 1):
            st.subheader(f"🏀 Equipo {i}")

            totales = {a: 0 for a in ATRIBUTOS}

            for j in equipo:
                st.write(
                    f"{j['Jugador']} "
                    f"(A:{j['Altura']} V:{j['Velocidad']} "
                    f"H:{j['Habilidad']} TI:{j['Tiro Interior']} TE:{j['Tiro Exterior']})"
                )

                for a in ATRIBUTOS:
                    totales[a] += j[a]

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
    valores = {a: st.slider(a, 1, 5, 3) for a in ATRIBUTOS}

    if st.form_submit_button("Guardar jugador"):
        nuevo = {"Jugador": nombre}
        nuevo.update(valores)
        guardar_jugador(nuevo)
        st.success("Jugador añadido correctamente")
        st.cache_data.clear()


