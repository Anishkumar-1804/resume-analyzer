import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import tempfile
import os
import fitz
import docx
import filetype
from PIL import Image
import google.generativeai as genai
from gemini_config import GEMINI_API_KEY
import time
import base64

# Gemini config
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# App config
st.set_page_config(
    page_title="Resume Genius | AI-Powered Resume Analyzer", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Embedded CSS ---
def set_css():
    st.markdown("""
    <style>
        body, .stApp {
            font-family: "Poppins", "Inter", sans-serif !important;
            background-color: #1f2235;
            color: #ffffff;
        }
        h1, h2, h3, h4 {
            color: #eebbc3;
            font-weight: 700;
        }
        .stContainer, .stCard, .stMarkdown div[data-testid="stMarkdownContainer"] {
            background: #282a3a;
            border-radius: 14px;
            padding: 1.4rem;
            color: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            border: 1.5px solid #a7f0ba;
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            background-color: #a7f0ba;
            color: #1f2235;
            border-radius: 6px;
            font-weight: 600;
            padding: 10px 24px;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #f4d06f;
            color: #1f2235;
        }
        .stFileUploader>div>div {
            border: 2px dashed #eebbc3;
            background: #1f223533;
            border-radius: 12px;
        }
        .stProgress>div>div>div {
            background-color: #65ccb8 !important;
        }
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            background: #1f2235;
        }
        ::-webkit-scrollbar-thumb {
            background: #a7f0ba;
            border-radius: 7px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #f4d06f;
        }
        a {
            color: #80d8ff;
        }
    </style>
    """, unsafe_allow_html=True)

set_css()

# --- Helper functions ---
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs])

def detect_file_type(path):
    kind = filetype.guess(path)
    return kind.extension if kind else path.split('.')[-1].lower()

def analyze_with_gemini(input_data, job_description=None):
    base_prompt = """
You are an expert resume reviewer with 15+ years of HR experience at top tech companies. 
Analyze this resume comprehensively and provide detailed feedback in the following structure:

### 🔍 Resume Overview
- Format assessment (ATS compatibility)
- Document structure evaluation
- First impressions summary

### 📊 Section-by-Section Analysis
For each detected section (Education, Experience, Skills, etc.):
1. **Rating**: /10 with justification
2. **Strengths**: Bullet points
3. **Improvements**: Actionable suggestions
4. **Keywords**: Missing industry terms

### 🎯 Targeted Recommendations
- Top 3 priority improvements
- Skills/experiences to highlight
- Redundant content to remove

### 💯 Overall Score: /100
With detailed breakdown:
- Content (40%)
- Structure (30%)
- Impact (20%)
- ATS Optimization (10%)

### ✨ Enhancement Suggestions
- Power verbs to incorporate
- Quantifiable achievements to add
- Modern formatting tips

Format your response in beautiful Markdown with emojis for visual scanning.
"""
    
    if job_description:
        base_prompt += f"\n\nAdditionally, optimize this resume for the following job description:\n{job_description}"
    
    response = model.generate_content([base_prompt, input_data])
    return response.text

def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- UI Components ---
def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem">
            <h2>Resume Genius</h2>
            <p>AI-Powered Resume Analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("⚙️ Analysis Settings", expanded=True):
            analysis_depth = st.select_slider(
                "Analysis Depth",
                options=["Basic", "Standard", "Comprehensive"],
                value="Standard"
            )
            
            ats_check = st.checkbox("Enable ATS Simulation", True)
            bias_check = st.checkbox("Reduce AI Bias", False)
        
        with st.expander("🎯 Job Targeting", expanded=False):
            job_title = st.text_input("Target Job Title")
            job_description = st.text_area("Paste Job Description")
        
        st.markdown("""
        **💡 Pro Tips:**
        - PDFs work best for analysis
        - Keep resumes under 3 pages
        - Remove personal contact info
        """)
        
        st.markdown("""
        <div style="text-align: center">
            <small>Powered by Gemini 1.5 Flash</small><br>
            <small>v2.1.0</small>
        </div>
        """, unsafe_allow_html=True)
        
        return {
            "analysis_depth": analysis_depth,
            "ats_check": ats_check,
            "bias_check": bias_check,
            "job_title": job_title,
            "job_description": job_description
        }

def upload_section():
    with stylable_container(
        key="upload_container",
        css_styles="""
            {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: calc(1em - 1px);
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            """
    ):
        st.markdown("""
        <div style="text-align: center; padding: 20px 0">
            <h3>📤 Upload Your Resume</h3>
            <p>We accept PDF, DOCX, and image files</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            return tmp_path, uploaded_file.name
    return None, None

def analysis_progress():
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 20:
            status_text.text("Extracting text content...")
        elif i < 50:
            status_text.text("Analyzing resume structure...")
        elif i < 80:
            status_text.text("Evaluating content quality...")
        else:
            status_text.text("Finalizing recommendations...")
        time.sleep(0.02)
    
    status_text.success("Analysis complete!")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()

# --- Main App ---
def main():
    # Sidebar
    settings = sidebar()
    
    # Main content
    st.markdown("<h2 style='text-align: center; color: #eebbc3;'>AI-Powered Resume Analysis</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin: 20px 0 40px">
        <p style="font-size: 1.1rem">
        Upload your resume and receive <strong>personalized, actionable feedback</strong> powered by Google's 
        most advanced AI. Our analysis covers content, structure, ATS optimization, and targeted improvements.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    file_path, file_name = upload_section()
    
    if file_path:
        ext = detect_file_type(file_path)
        input_data = None
        
        # Layout
        col1, col2 = st.columns([1.2, 2], gap="large")
        
        with col1:
            with stylable_container(
                key="preview_box",
                css_styles="""
                    {
                        border: 1px solid rgba(49, 51, 63, 0.2);
                        border-radius: 0.5rem;
                        padding: 1rem;
                        background: white;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    """
            ):
                st.markdown(f"### 📄 {file_name}")
                
                try:
                    if ext in ["jpg", "jpeg", "png"]:
                        image = Image.open(file_path).convert("RGB")
                        input_data = image
                        st.image(image, use_column_width=True)
                    elif ext == "pdf":
                        display_pdf(file_path)
                        text = extract_text_from_pdf(file_path)
                        input_data = text
                    elif ext == "docx":
                        text = extract_text_from_docx(file_path)
                        input_data = text
                        st.warning("DOCX preview not available. Content will still be analyzed.")
                except Exception as e:
                    st.error(f"Error processing file: {e}")
                    os.remove(file_path)
                    return
        
        with col2:
            if st.button("**🔍 Analyze Resume**", type="primary", use_container_width=True):
                analysis_progress()
                
                with stylable_container(
                    key="results_box",
                    css_styles="""
                        {
                            border: 1px solid rgba(49, 51, 63, 0.2);
                            border-radius: 0.5rem;
                            padding: 1rem;
                            background: white;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        }
                        """
                ):
                    with st.spinner("Generating comprehensive analysis..."):
                        try:
                            analysis = analyze_with_gemini(
                                input_data, 
                                settings["job_description"] if settings["job_description"] else None
                            )
                            st.markdown(analysis, unsafe_allow_html=True)
                            
                            # Download button for the analysis
                            st.download_button(
                                label="📥 Download Analysis Report",
                                data=analysis,
                                file_name="resume_analysis_report.md",
                                mime="text/markdown",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Analysis error: {str(e)}")
                
                # Additional recommendations
                with st.expander("🚀 Personalized Action Plan", expanded=True):
                    st.info("""
                    **Next Steps Based on Your Analysis:**
                    - Implement the top 3 priority improvements first
                    - Use the suggested power verbs in your experience section
                    - Consider our formatting recommendations for better visual hierarchy
                    """)
        
        os.remove(file_path)
    
    else:
        # Show demo or features if no file uploaded
        with stylable_container(
            key="features_container",
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 1rem;
                    background: white;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                """
        ):
            st.markdown("""
            ## ✨ What You'll Get
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin: 1rem 0">
                <div style="padding: 1rem; background: #f8f9fa; border-radius: 0.5rem">
                    <h4>🔍 ATS Optimization</h4>
                    <p>Identify keywords and formatting issues that affect applicant tracking systems</p>
                </div>
                <div style="padding: 1rem; background: #f8f9fa; border-radius: 0.5rem">
                    <h4>📊 Content Scoring</h4>
                    <p>Detailed ratings for each section with specific improvement suggestions</p>
                </div>
                <div style="padding: 1rem; background: #f8f9fa; border-radius: 0.5rem">
                    <h4>🎯 Targeted Feedback</h4>
                    <p>Personalized recommendations based on your target job and industry</p>
                </div>
                <div style="padding: 1rem; background: #f8f9fa; border-radius: 0.5rem">
                    <h4>💎 Pro Enhancements</h4>
                    <p>Advanced tips to make your resume stand out to hiring managers</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            
if __name__ == "__main__":
    main()