import streamlit as st
import PyPDF2
import openai
import os

client = openai.Client(
    api_key=os.getenv("OPENAI_API_KEY")
)


def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def generate_blog_ideas(text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates blog post long-tail SEO ideas based on the given text."},
            {"role": "user", "content": f"Generate 10 blog post ideas with long-tail SEO titles based on the following text:\n\n{text[:2000]}\nReturn in the following format (separate by commas, don't leave spaces or empty lines): idea_1,idea_2,idea_3,idea_n"}
        ]
    )

    return response.choices[0].message.content.split(',')

def generate_full_blog(idea):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes a 3 pages blog posts based on given ideas."},
            {"role": "user", "content": f"Write a full blog post based on the following idea in the language of the idea:\n\n{idea}"}
        ]
    )
    return response.choices[0].message.content

def main():
    st.title("Blog Generator de PDF - SquadS PoC")

    uploaded_file = st.file_uploader("Selecciona un archivo formato PDF", type="pdf")

    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
        st.success("PDF subido y extraido exitosamente!")

        if st.button("Genera tus ideas de blog"):
            with st.spinner("Generando ideas para tus blogs..."):
                ideas = generate_blog_ideas(text)
                st.session_state.ideas = ideas

        if 'ideas' in st.session_state:
            st.subheader("Ideas generadas:")
            for i, idea in enumerate(st.session_state.ideas):
                if st.button(f"Idea {i+1}: {idea}"):
                    with st.spinner("Generando full blog post..."):
                        full_blog = generate_full_blog(idea)
                        st.subheader(f"Full Blog Post para idea {i+1}")
                        st.write(full_blog)

if __name__ == "__main__":
    main()
