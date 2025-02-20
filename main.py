import os  # Permite acceder a variables de entorno
import streamlit as st  # Para crear la interfaz de usuario
from dotenv import load_dotenv  # Para cargar variables desde un archivo .env
from groq import Groq  # Cliente para comunicarse con la API de Groq
from loguru import logger  # Para gestionar logs y mensajes en consola
from openai import OpenAI  # Cliente para interactuar con la API de OpenAI
import pandas as pd  # Para manejar archivos CSV y Excel
import matplotlib.pyplot as plt  # Para generar gráficos

load_dotenv()  # Carga las variables de entorno
logger.info(os.getenv('GROQ_API_KEY'))  # Registra la clave en la consola

# Clientes para los modelos
qclient = Groq()
client = OpenAI()

# Creación de la interfaz con Streamlit
st.title('📊 Predicción Electoral 2025')
st.markdown('---')
st.subheader('Resultados del Conteo de Votos')

# Función para extraer datos de un archivo CSV o Excel
def load_data(file):
    file_extension = file.name.split(".")[-1]
    if file_extension == "csv":
        df = pd.read_csv(file)
    elif file_extension == "xlsx":
        df = pd.read_excel(file)
    return df

# Opción para subir un archivo
uploaded_file = st.file_uploader("📤 Sube un archivo CSV o Excel con los votos", type=["csv", "xlsx"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.write("### 📜 Datos del Archivo")
    st.dataframe(df)

    # Generar gráfica de barras
    st.write("### 📊 Gráfico de Votos")
    fig, ax = plt.subplots()
    df.set_index(df.columns[0]).plot(kind='bar', ax=ax, colormap='viridis')
    st.pyplot(fig)

    # Guardar resultados en Excel
    output_file = "resultados_prediccion.xlsx"
    df.to_excel(output_file, index=False)
    with open(output_file, "rb") as f:
        st.download_button("📥 Descargar Resultados en Excel", f, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Gestión de mensajes
if 'messages' not in st.session_state:
    st.session_state.messages = []

for messages in st.session_state.messages:
    with st.chat_message(messages['role']):
        st.markdown(messages['content'])

# Función para procesar la respuesta del modelo
def process_data(chat_completion) -> str:
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Entrada del usuario
if prompt := st.chat_input('✍️ Ingresa una consulta sobre los resultados'):
    with st.chat_message('user'):
        st.markdown(prompt)

    st.session_state.messages.append({'role': 'user', 'content': prompt})

    with st.chat_message('assistant'):
        stream_response = qclient.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analizador electoral que extrae solo los Votos Luisa, Votos  Noboa y Votos Nulos y presenta con etiquetas el nombre y el valor, por ejemplo Voto Noboa = 100, Voto Luisa =50, Voto Nulo = 10",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            model="llama3-8B-8192",
            stream=True
        )
        
        response = process_data(stream_response)
        response = st.write_stream(response)

    st.session_state.messages.append({'role': 'assistant', 'content': response})

