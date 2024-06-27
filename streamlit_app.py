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
            {"role": "system", "content": f"Eres un asistente til que escribe blogs de 10k caracteres y 7 subtítulos basados en ideas dadas. El tono de voz para inspirarte es: {tone}"},
            {"role": "user", "content": f"Escribe un blog completo de más de 10 mil caracteres con 7 subtítulos basado en la siguiente idea en el idioma de la idea:\n\n{idea}. Inspirado en el siguiente texto:\n\n{text[:2000]}"}
        ]
    )
    return response.choices[0].message.content

def main():
    st.title("Generador de Blogs - SquadS PoC")

    if 'text' not in st.session_state:
        st.session_state.text = None

    input_type = st.radio("Selecciona el tipo de entrada:", ("PDF", "Video de YouTube"))

    if input_type == "PDF":
        uploaded_file = st.file_uploader("Selecciona un archivo PDF", type="pdf")
        if uploaded_file is not None:
            st.session_state.text = extract_text_from_pdf(uploaded_file)
            st.success("¡PDF subido y extraído exitosamente!")
    else:
        youtube_url = st.text_input("Ingresa la URL del video de YouTube")
        if youtube_url and st.session_state.text is None:
            with st.spinner("Descargando y transcribiendo el video..."):
                audio_file = download_youtube_audio(youtube_url)
                st.session_state.text = transcribe_audio(audio_file)
                os.unlink(audio_file)  # Eliminar el archivo temporal
            st.success("¡Video transcrito exitosamente!")

    if st.session_state.text is not None:
        tone = st.text_input("Ingresa el tono de voz para inspirar la creación del blog (por ejemplo: profesional, casual, humorístico, etc.)")

        if st.button("Generar ideas de blog"):
            with st.spinner("Generando ideas de blog..."):
                ideas = generate_blog_ideas(st.session_state.text)
                st.session_state.ideas = ideas

        if 'ideas' in st.session_state:
            st.subheader("Ideas generadas:")
            for i, idea in enumerate(st.session_state.ideas):
                if st.button(f"Idea {i+1}: {idea}"):
                    with st.spinner("Generando blog completo..."):
                        full_blog = generate_full_blog(idea, tone, st.session_state.text)
                        st.subheader(f"{idea}")
                        st.write(full_blog)

if __name__ == "__main__":
    main()
