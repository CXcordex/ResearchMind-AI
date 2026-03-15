import streamlit as st
import pickle
import nltk
import re

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="AI Resume Screener", page_icon="📄", layout="wide")

def local_css():
    st.markdown("""
        <style>
        /* Background Gradient */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* Title Styling */
        .main-title {
            color: #2c3e50;
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            margin-bottom: 10px;
        }
        
        /* Prediction Box */
        .result-container {
            background-color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 8px solid #4a90e2;
            text-align: center;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. ASSETS & MODELS ---
@st.cache_resource
def load_models():
    nltk.download('stopwords')
    nltk.download('punkt')
    clf = pickle.load(open('resume_screening_model.pkl', 'rb'))
    tfidf = pickle.load(open('tfidf_model.pkl', 'rb'))
    le = pickle.load(open('label-encoder.pkl', 'rb'))
    return clf, tfidf, le

clf, tfidf, le = load_models()

def clean_data(txt):
    clean_text = re.sub(r'https\S+\s*', '', txt)
    clean_text = re.sub(r'RT|CC', '', clean_text)
    clean_text = re.sub(r'#\S+', '', clean_text)
    clean_text = re.sub(r'@\S+', '', clean_text)
    clean_text = re.sub(r'[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), '', clean_text)
    clean_text = re.sub(r'[^\x00-\x7f]', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

# --- 3. UI LAYOUT ---
st.markdown('<h1 class="main-title">🚀 Resume Screening AI</h1>', unsafe_allow_html=True)
st.write("<p style='text-align: center; color: #5d6d7e;'>Upload a professional CV to determine the best job category match instantly.</p>", unsafe_allow_html=True)
st.write("---")

# Sidebar for instructions
with st.sidebar:
    st.header("How it works")
    st.info("""
    1. Upload a resume (PDF/TXT/DOCX).
    2. Our NLP model cleans the text.
    3. The AI predicts the job category based on your skills.
    """)
    st.warning("Ensure the file is not password protected.")

# Main Interface
col1, col2 = st.columns([2, 1])

with col1:
    upload = st.file_uploader("Drop your resume here", type=["pdf", "docx", "txt"])

if upload is not None:
    with col2:
        with st.status("Analyzing resume...", expanded=True):
            try:
                resume_bytes = upload.read()
                resume_text = resume_bytes.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                resume_text = resume_bytes.decode('latin-1', errors='ignore')
            
            # Prediction Logic
            clean_resume = clean_data(resume_text)
            vectorized_resume = tfidf.transform([clean_resume])
            prediction1 = clf.predict(vectorized_resume)
            category = le.inverse_transform([prediction1])[0]
            st.write("Analysis Complete!")

    # Display Result in a styled Card
    st.markdown(f"""
        <div class="result-container">
            <h3 style="color: #7f8c8d; margin-bottom: 0;">Predicted Job Category:</h3>
            <h1 style="color: #4a90e2; font-size: 3.5rem; margin-top: 10px;">{category}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Optional: Display a preview of the cleaned text
    with st.expander("View Cleaned Text Preview"):
        st.text(clean_resume[:500] + "...")

else:
    st.info("Waiting for file upload...")

# Footer
st.markdown("---")
st.caption("Developed by Sayan Roy Chowdhury | Powered by Streamlit & NLP")