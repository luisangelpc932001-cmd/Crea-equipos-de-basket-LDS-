import streamlit as st
import pandas as pd
import random
import unicodedata

# =========================
# CONFIG
# =========================
ARCHIVO = r"Jugadores 1.xlsx"

ATRIBUTOS = ["Altura", "Velocidad", "Habilidad", "Tiro Interior", "Tiro Exterior"]
LIMITE = 20  # ✅ ahora TODAS las habilidades tienen máximo 20

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
@st.cache_data
def cargar_jugadores():
    df = pd.read_excel(ARCHIVO)
    df.columns = ["Jugador"] + ATRIBUTOS
    df["Jugador_norm"] = df["Jugador"].apply(normalizar)
    return df


# =========================
# GUARDAR NUEVO JUGADOR
# =========================
def guardar_jugador(jugador):
    df = pd.read_excel(ARCHIVO)
    df.columns = ["Jugador"] + ATRIBUTOS
    df = pd.concat([df, pd.DataFrame([jugador])], ignore_index=True)
    df.to_excel(ARCHIVO, index=False)


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
            # ✅ mismo máximo (20) para todas las habilidades
            if stats_equipo[attr] + jugador[attr] > LIMITE:
                return False

            valores = [j[attr] for j in equipo]

            # ❌ no más de un 5 por atributo
            if jugador[attr] == 5 and 5 in valores:
                return False

        # =========================
        # REGLAS DE ALTURA (sin cambios)
        # =========================
        alturas = [j["Altura"] for j in equipo]

        # máximo un 5
        if jugador["Altura"] == 5 and alturas.count(5) >= 1:
            return False

        # máximo dos 4
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
        nuevo = {"Jugador": nombre}
        nuevo.update(valores)
        guardar_jugador(nuevo)
        st.success("Jugador añadido correctamente")
        st.cache_data.clear()


