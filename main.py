import streamlit as st
import requests
import feedparser
import pdfplumber
import os
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def generate_query(title, about):
    logging.info("Starting query generation")
    api_key = "AIzaSyC4W72QzE7TUzHfD2qjb6Nma6kZmyBHGQg"  # Replace with your actual API key
    if api_key:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
            Generate a concise search query for arXiv based on the following information:
            Title: {title}
            About the Paper: {about}
            The query should be clear, relevant, and suitable for retrieving academic papers related to the given title and description.
        """
        res = model.generate_content(prompt)
        logging.info("Query generated successfully")
        return sanitize_query(res.text.strip())
    logging.error("API key not configured")
    return ""

def sanitize_query(query):
    sanitized_query = query
    sanitized_query = sanitized_query.replace('(', '').replace(')', '')  # Remove parentheses
    sanitized_query = sanitized_query.replace('"', '').replace("'", '')  # Remove single and double quotes
    sanitized_query = ' '.join(sanitized_query.split())  # Remove extra spaces
    return sanitized_query

def search_and_process_arxiv(query, max_results=5, sort_by="relevance"):
    logging.info("Starting arXiv search")
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query={query.replace(' ', '+')}&max_results={max_results}&sortBy={sort_by}"

    try:
        response = requests.get(base_url + search_query)
        response.raise_for_status()
        logging.info("Data fetched from arXiv successfully")
    except requests.RequestException as e:
        logging.error(f"Error fetching data from arXiv: {e}")
        return "", f"Error fetching data from arXiv: {e}"

    feed = feedparser.parse(response.text)

    if not feed.entries:
        logging.info("No results found on arXiv")
        return "", "No results found."

    pdf_dir = "arxiv_papers"
    os.makedirs(pdf_dir, exist_ok=True)

    combined_text = ""

    for paper in feed.entries:
        if "v1" not in paper.id:
            continue

        title = paper.title
        paper_link = paper.link
        pdf_url = paper.id.replace('abs', 'pdf') + ".pdf"
        pdf_filename = os.path.join(pdf_dir, f"{sanitize_filename(title)}.pdf")

        if download_pdf(pdf_url, pdf_filename):
            text = extract_text_from_pdf(pdf_filename)
            combined_text += f"Title: {title}\nLink: {paper_link}\n\n{text}\n\n"
        else:
            logging.error(f"Failed to download or process: {title}")
            return "", f"Failed to download or process: {title}"

    logging.info("Processing completed successfully")
    return combined_text, None

def download_pdf(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as file:
            file.write(response.content)
        logging.info(f"PDF downloaded: {filename}")
        return True
    except requests.RequestException as e:
        logging.error(f"Error downloading PDF: {e}")
        return False
    except IOError as e:
        logging.error(f"Error saving PDF: {e}")
        return False

def extract_text_from_pdf(filename):
    text = ""
    try:
        with pdfplumber.open(filename) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
    return text

def sanitize_filename(filename):
    return filename.replace(' ', '_').replace(':', '').replace('/', '')

def generate_literature_survey(text):
    logging.info("Starting literature survey generation")
    api_key = "AIzaSyC4W72QzE7TUzHfD2qjb6Nma6kZmyBHGQg"  # Replace with your actual API key
    if api_key:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
            You are an expert research scientist with years of experience in analyzing and writing literature reviews for research papers. Your task is to apply your expertise to craft a comprehensive literature review for the paper titled [Title]. The review will focus on [Description]. You will be given the necessary research papers and materials for you to look over.
            Follow the following rules strictly:
            -Structure the content clearly, precisely and in long paragraphs without breaking into points
            -Using APA citation style.
            -Analyze and discuss the methods used in the studies and the results obtained.
            -Ensure that your writing flows smoothly between paragraphs
            -Keep the review insightful, engaging, and informative while maintaining a formal academic tone.
            - At the end provide reference list
            
            **Text:**

            {text}
        """
        res = model.generate_content(prompt)
        logging.info("Literature survey generated successfully")
        return res.text
    logging.error("API key not configured")
    return ""

def main():
    st.markdown("""
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f4;
            }
            .main-content {
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }
            .stButton button {
                background-color: #007bff !important;
                color: white !important;
                border: none !important;
                border-radius: 4px !important;
                padding: 0.5rem 1rem !important;
            }
            .stButton button:hover {
                background-color: #0056b3 !important;
            }
            footer {
                margin-top: 2rem;
                background-color: #f1f1f1;
                padding: 10px;
                text-align: center;
            }
            footer a {
                text-decoration: none;
                color: #007bff;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    st.title("Literature Survey Generator 📚")

    option = st.radio("Choose an option to generate a literature survey:", ("By Title and Description", "By Uploading Paper(s)"))

    if option == "By Title and Description":
        title = st.text_input("Enter the Title of the Paper:")
        about = st.text_area("Enter the Description About the Paper:")

        if st.button("Generate Literature Survey"):
            with st.spinner("Generating query..."):
                query = generate_query(title, about)
            if not query:
                st.error("Failed to generate a query.")
                return

            with st.spinner("Fetching and processing papers..."):
                text, error = search_and_process_arxiv(query, max_results=5, sort_by="relevance")
            if error:
                st.error(error)
            else:
                with st.spinner("Generating literature survey..."):
                    survey = generate_literature_survey(text)  # Correctly use extracted text
                st.write("### Generated Literature Survey")
                st.write(survey)

    elif option == "By Uploading Paper(s)":
        uploaded_files = st.file_uploader("Upload one or more PDF files", type="pdf", accept_multiple_files=True)

        if uploaded_files:
            combined_text = ""
            for idx, uploaded_file in enumerate(uploaded_files):
                with pdfplumber.open(uploaded_file) as pdf:
                    paper_text = ""
                    for page in pdf.pages:
                        paper_text += page.extract_text() or ""
                    combined_text += f"Paper {idx + 1}:\n{paper_text}\n\n"

            if st.button("Generate Literature Survey"):
                with st.spinner("Generating literature survey..."):
                    survey = generate_literature_survey(combined_text)  # Use extracted text from uploaded papers
                st.write("### Generated Literature Survey")
                st.write(survey)

    st.markdown("</div>", unsafe_allow_html=True)

    # Adding credits with hyperlinks
    st.markdown("""
        <footer>
            <p>Made by <a href="https://www.linkedin.com/in/vansh-jatana/" target="_blank">Vansh Jatana</a> and <a href="https://www.linkedin.com/in/raghavventure/" target="_blank">Raghav Gupta</a></p>
        </footer>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
