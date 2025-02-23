import os  # carga variables de entorno
import streamlit as st  # interfaz web
from dotenv import load_dotenv  # cargar las variables de .env
from groq import Groq  # interactuar con la API de Groq (IA).
from loguru import logger  # maneja logs y mensajes en consola
from openai import OpenAI  # para el chat bot
import pandas as pd  # trabajar con csv
import matplotlib.pyplot as plt  # gráficas
import random  # valores aleatorios

# Cargar variables de entorno
load_dotenv()
logger.info(os.getenv('GROQ_API_KEY'))

# Inicializar clientes
qclient = Groq()
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))  # Cliente de OpenAI para el chatbot

# Pantalla de inicio
st.title('📊 Predicción Electoral 2025')
st.markdown('---')
st.subheader('Resultados del Conteo de Votos')

# Función para cargar datos
def load_data(file):
    df = pd.read_excel(file)
    return df

# Cargar archivo
uploaded_file = st.file_uploader("📤 Sube un archivo Excel con los votos", type=["xlsx"])

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Verificar si la columna 'text' existe
    if 'text' not in df.columns:
        st.error("❌ El archivo no contiene una columna llamada 'text'. Verifica el formato.")
    else:
        st.write("### 📜 Datos del Archivo")
        st.dataframe(df[['text']])  # Mostrar solo la columna 'text'

        # Muestra aleatoria controlable
        sample_size = st.slider("Cantidad de datos a mostrar", 1, len(df), 30)
        random_state = random.randint(1, 100)  # Estado aleatorio para reproducibilidad
        df_sample = df.sample(n=sample_size, random_state=random_state)  # Muestra aleatoria

        st.write("### 📌 Muestra de Datos")
        st.dataframe(df_sample[['text']])

        # Análisis de votos basado en comentarios
        st.write("### 🏷️ Clasificación de Votos")

        def classify_vote(text):
            text = str(text).lower()  # Convertir a minúsculas para evitar problemas de mayúsculas
            if "noboa" in text:
                return "Voto Noboa"
            elif "luisa" in text:
                return "Voto Luisa"
            elif "nulo" in text:
                return "Voto Nulo"
            else:
                return "Voto Nulo"  # Si no se encuentra coincidencia, se considera nulo

        df_sample["Clasificación"] = df_sample["text"].apply(classify_vote)

        # Contar votos
        vote_counts = df_sample["Clasificación"].value_counts().to_dict()

        st.write("### 🗳️ Resultados de la Muestra Aleatoria")
        st.json(vote_counts)

        # Gráfico de barras
        st.write("### 📊 Gráfico de Votos (Muestra Aleatoria)")
        fig, ax = plt.subplots()
        colors = {'Voto Noboa': 'blue', 'Voto Luisa': 'red', 'Voto Nulo': 'gray'}
        ax.bar(vote_counts.keys(), vote_counts.values(), color=[colors[key] for key in vote_counts.keys()])
        st.pyplot(fig)

        # Conclusión sobre votos nulos
        st.write("### 📢 Análisis de Votos Nulos (Muestra Aleatoria)")
        if vote_counts.get("Voto Nulo", 0) > (vote_counts.get("Voto Noboa", 0) + vote_counts.get("Voto Luisa", 0)) / 2:
            st.warning("⚠️ Hay una cantidad significativa de votos nulos, lo que podría indicar problemas en la votación.")
        else:
            st.success("✅ La cantidad de votos nulos es baja, lo que sugiere una elección clara.")

        # Descargar resultados de la muestra
        output_file = "resultados_muestra_aleatoria.xlsx"
        df_sample.to_excel(output_file, index=False)
        with open(output_file, "rb") as f:
            st.download_button("📥 Descargar Muestra Aleatoria en Excel", f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Chatbot
st.markdown('---')
st.subheader('🤖 Chatbot de Asistencia')

# Inicializar el historial del chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada del usuario
if prompt := st.chat_input("¿En qué puedo ayudarte?"):
    # Agregar el mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta del chatbot
    with st.chat_message("assistant"):
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Puedes cambiar el modelo si lo prefieres
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        )
        assistant_response = response.choices[0].message.content
        st.markdown(assistant_response)

    # Agregar la respuesta del asistente al historial
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})