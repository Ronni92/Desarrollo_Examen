import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from groq import Groq
import random
import json

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente de Groq
qclient = Groq()

# Configuración de la app
st.title('📊 Predicción Electoral 2025')
st.markdown('---')
st.subheader('Resultados del Conteo de Votos')

# Función para cargar datos
def load_data(file):
    df = pd.read_excel(file, usecols=["text"])
    return df

# Función para clasificar un texto completo
def classify_text(text):
    response = qclient.chat.completions.create(
        messages=[
            {"role": "system", "content": "Eres un analista electoral experto en interpretar el contexto de los textos, Clasifica cada texto de acuerdo con su contenido:Si el texto apoya o menciona positivamente a Luisa, responde únicamente con: 'Voto Luisa',Si el texto apoya o menciona positivamente a Noboa, responde únicamente con: 'Voto Noboa',Si el texto no menciona a ninguno o es neutral, responde únicamente con: 'Voto Nulo',solo responde con una de las tres opciones"},
            {"role": "user", "content": text}
        ],
        model="llama3-8B-8192",
        max_tokens=10,
        temperature=0.1
    )
    return response.choices[0].message.content.strip()

# Cargar archivo
uploaded_file = st.file_uploader("📤 Sube un archivo Excel", type=["xlsx"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.write("### 📜 Datos del Archivo ('text')")
    st.dataframe(df)

    # Muestra aleatoria
    sample_size = st.slider("Cantidad de datos a analizar", 1, len(df), 15)
    df_sample = df.sample(n=sample_size, random_state=random.randint(1, 100))
    st.write("### 📌 Muestra de Datos")
    st.dataframe(df_sample)

    # Contadores de votos (inicializados con todas las clasificaciones posibles)
    vote_counts = {"Voto Luisa": 0, "Voto Noboa": 0, "Voto Nulo": 0}
    classified_results = []

    st.write("### 🧠 Clasificando votos...")
    
    for _, row in df_sample.iterrows():
        text = row["text"]
        if pd.isna(text):
            continue
        
        classification = classify_text(text)
        
        # Verificar si la clasificación es válida antes de incrementar el contador
        if classification in vote_counts:
            vote_counts[classification] += 1
            classified_results.append({"text": text, "clasificación": classification})
        else:
            st.warning(f"⚠️ Clasificación no válida: {classification} en el texto: '{text}'")
    
    # Mostrar resultados JSON
    st.write("### 📊 Resultados del Conteo de Votos")
    st.json(classified_results)
    st.write("### 📊 Resumen Total de Votos")
    st.json(vote_counts)

    # Generar gráfico
    fig, ax = plt.subplots()
    ax.bar(vote_counts.keys(), vote_counts.values(), color=['red', 'blue', 'gray'])
    st.pyplot(fig)

    # Análisis de votos nulos
    st.write("### 📢 Análisis de Votos Nulos")
    if vote_counts["Voto Nulo"] > (vote_counts["Voto Noboa"] + vote_counts["Voto Luisa"]) / 2:
        st.warning("⚠️ Alta cantidad de votos nulos, lo que podría indicar problemas en la votación.")
    else:
        st.success("✅ Baja cantidad de votos nulos, lo que sugiere una elección clara.")
    
    # Chatbot para preguntas sobre los resultados
    st.write("### 🤖 Preguntas sobre los resultados")
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for messages in st.session_state.messages:
        with st.chat_message(messages['role']):
            st.markdown(messages['content'])

    if prompt := st.chat_input('✍️ Ingresa una consulta sobre los resultados'):
        with st.chat_message('user'):
            st.markdown(prompt)
        
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        
        with st.chat_message('assistant'):
            stream_response = qclient.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un experto analizador electoral. Analiza la información y proporciona respuestas sobre los resultados del conteo de votos."},
                    {"role": "user", "content": prompt},
                ],
                model="llama3-8B-8192",
                stream=True
            )
            response = "".join(chunk.choices[0].delta.content for chunk in stream_response if chunk.choices[0].delta.content)
            st.markdown(response)
        
        st.session_state.messages.append({'role': 'assistant', 'content': response})