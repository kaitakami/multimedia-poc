import streamlit as st
import PyPDF2
import openai
import os
from pytube import YouTube
import tempfile

client = openai.Client(
    api_key=os.getenv("OPENAI_API_KEY")
)


def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def download_youtube_audio(url):
    yt = YouTube(url)
    audio = yt.streams.filter(only_audio=True).first()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
        audio.download(filename=temp_file.name)
        return temp_file.name

def transcribe_audio(audio_file):
    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=file
        )
    return transcription.text

def generate_blog_ideas(text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente útil que genera ideas de blogs con títulos SEO de cola larga basados en el texto proporcionado."},
            {"role": "user", "content": f"Genera 10 ideas de blogs con títulos SEO de cola larga basados en el siguiente texto:\n\n{text[:2000]}\nDevuelve en el siguiente formato (separado por comas, sin espacios ni líneas vacías): idea_1,idea_2,idea_3,idea_n"}
        ]
    )
    return response.choices[0].message.content.split(',')

def generate_full_blog(idea, tone, text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Eres un asistente útil que escribe blogs de 10k caracteres y 7 subtítulos basados en ideas dadas. El tono de voz para inspirarte es: {tone}"},
            {"role": "user", "content": f"Escribe un blog completo de más de 10 mil caracteres con 7 subtítulos basado en la siguiente idea en el idioma de la idea:\n\n{idea}. Inspirado en el siguiente texto:\n\n{text[:2000]}"}
        ]
    )
    return response.choices[0].message.content

def reset_state():
    for key in ['text', 'ideas', 'full_blog', 'tone', 'last_youtube_url']:
        if key in st.session_state:
            del st.session_state[key]

def main():
    st.title("Generador de Blogs Flexible - SquadS PoC")

    # Reset button
    if st.button("Reiniciar"):
        reset_state()
        st.rerun()

    # Input type selection
    input_type = st.radio("Selecciona el tipo de entrada:", 
                          ("PDF", "Video de YouTube", "Twitter", "Instagram", "Texto personalizado"))

    # Input handling based on type
    if input_type == "PDF":
        uploaded_file = st.file_uploader("Selecciona un archivo PDF", type="pdf")
        if uploaded_file is not None:
            st.session_state.text = extract_text_from_pdf(uploaded_file)
            st.success("¡PDF subido y extraído exitosamente!")
    elif input_type == "Video de YouTube":
        youtube_url = st.text_input("Ingresa la URL del video de YouTube")
        if youtube_url and youtube_url != st.session_state.get('last_youtube_url', ''):
            with st.spinner("Descargando y transcribiendo el video..."):
                audio_file = download_youtube_audio(youtube_url)
                st.session_state.text = transcribe_audio(audio_file)
                os.unlink(audio_file)  # Eliminar el archivo temporal
            st.session_state.last_youtube_url = youtube_url
            st.success("¡Video transcrito exitosamente!")
    elif input_type in ["Twitter", "Instagram", "Texto personalizado"]:
        st.text_area_label = {
            "Twitter": "Pega el contenido del tweet aquí",
            "Instagram": "Pega el contenido del post de Instagram aquí",
            "Texto personalizado": "Ingresa tu texto personalizado aquí"
        }[input_type]
        user_input = st.text_area(st.text_area_label, height=150)
        if user_input:
            st.session_state.text = user_input
            st.success(f"¡Contenido de {input_type} ingresado exitosamente!")

    # Tone input and idea generation
    if 'text' in st.session_state and st.session_state.text:
        tone = st.text_input("Ingresa el tono de voz para inspirar la creación del blog (por ejemplo: profesional, casual, humorístico, etc.)", key="tone")

        if st.button("Generar ideas de blog"):
            with st.spinner("Generando ideas de blog..."):
                st.session_state.ideas = generate_blog_ideas(st.session_state.text)

    # Display generated ideas and allow blog generation
    if 'ideas' in st.session_state and st.session_state.ideas:
        st.subheader("Ideas generadas:")
        for i, idea in enumerate(st.session_state.ideas):
            if st.button(f"Idea {i+1}: {idea}"):
                with st.spinner("Generando blog completo..."):
                    full_blog = generate_full_blog(idea, st.session_state.tone, st.session_state.text)
                    st.session_state.full_blog = full_blog
                    st.session_state.selected_idea = idea

    # Display generated blog
    if 'full_blog' in st.session_state:
        st.subheader(f"{st.session_state.selected_idea}")
        st.write(st.session_state.full_blog)

if __name__ == "__main__":
    main()