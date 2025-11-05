import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MediView AI - Medical Report Analysis",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR MEDICAL THEME ---
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        font-weight: bold;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        padding-bottom: 2rem;
    }
    .info-box {
        color: black;
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        margin: 1rem 0;
    }
    .warning-box {
        color:black;
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- API KEY CONFIGURATION ---
def get_api_key():
    """API key ko safely retrieve karta hai"""
    try:
        # Streamlit secrets se (deployment ke liye)
        if "google" in st.secrets and "GOOGLE_API_KEY" in st.secrets["google"]:
            return st.secrets["google"]["GOOGLE_API_KEY"]
    except:
        pass
    
    # Environment variable se (local testing ke liye)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return api_key
    
    return None

# API Key setup
GOOGLE_API_KEY = get_api_key()

if not GOOGLE_API_KEY:
    st.error("⚠️ GOOGLE_API_KEY not found! Please set it in Streamlit secrets or environment variables.")
    st.info("""
    **Setup Instructions:**
    - **For Local:** Set environment variable: `export GOOGLE_API_KEY='your_key_here'`
    - **For Streamlit Cloud:** Add to `.streamlit/secrets.toml`:
    ```
    [google]
    GOOGLE_API_KEY = "your_key_here"
    ```
    """)
    st.stop()

# Configure Gemini AI
genai.configure(api_key=GOOGLE_API_KEY)

# --- MODEL INITIALIZATION ---
@st.cache_resource
def initialize_model():
    """Model ko initialize karta hai (cached rahega)"""
    try:
        return genai.GenerativeModel('models/gemini-2.0-flash-exp')
    except Exception as e:
        st.error(f"Model initialization error: {e}")
        st.stop()

model = initialize_model()

# --- HEADER SECTION ---
st.markdown('<h1 class="main-header">🏥 MediView AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Medical Report Analysis & Health Insights Platform</p>', unsafe_allow_html=True)

# --- DISCLAIMER ---
st.markdown("""
<div class="warning-box">
    <strong>⚠️ Medical Disclaimer:</strong> This tool provides AI-generated insights for educational purposes only. 
    Always consult qualified healthcare professionals for medical advice, diagnosis, or treatment decisions.
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("medical_heart.png", width=80)
    st.title("📋 Analysis Options")
    
    # Input mode selection
    input_mode = st.radio(
        "Choose Input Method:",
        ["📄 Upload Report Image", "✍️ Enter Report Text"],
        help="Select how you want to provide your medical report"
    )
    
    st.markdown("---")
    
    # Analysis type
    analysis_type = st.selectbox(
        "Analysis Type:",
        [
            "🔍 Simple Explanation",
            "📊 Detailed Analysis",
            "💊 Health Recommendations",
            "📈 Trend Analysis",
            "🩺 All-in-One Report"
        ]
    )
    
    st.markdown("---")
    
    # Language preference
    language_pref = st.selectbox(
        "Preferred Language:",
        ["English", "Hinglish", "Hindi", "Match My Input"]
    )
    
    st.markdown("---")
    
    # Report type (optional context)
    report_type = st.selectbox(
        "Report Type (Optional):",
        [
            "General",
            "Blood Test / CBC",
            "Lipid Profile",
            "Liver Function Test",
            "Kidney Function Test",
            "Thyroid Test",
            "Diabetes (HbA1c/Glucose)",
            "Vitamin Levels",
            "X-Ray Report",
            "Other"
        ]
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Upload clear images for better accuracy!")

# --- MAIN CONTENT AREA ---
col1, col2 = st.columns([1, 1])

# --- LEFT COLUMN: INPUT ---
with col1:
    st.subheader("📥 Input Your Medical Report")
    
    uploaded_file = None
    text_input = None
    
    if input_mode == "📄 Upload Report Image":
        uploaded_file = st.file_uploader(
            "Upload Medical Report Image",
            type=["jpg", "jpeg", "png", "pdf"],
            help="Supported formats: JPG, JPEG, PNG"
        )
        
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.image(img, caption="Uploaded Report", use_container_width=True)
            
    else:  # Text input mode
        text_input = st.text_area(
            "Paste or Type Your Report Data:",
            height=300,
            placeholder="Example:\nHemoglobin: 13.5 g/dL\nWBC Count: 7500 cells/μL\nPlatelet Count: 250,000/μL\n..."
        )
        
        if text_input:
            st.success("✅ Text input received!")
    
    # Optional: Report name/date
    report_name = st.text_input(
        "Report Name (Optional):",
        placeholder="e.g., Blood Test - Jan 2024"
    )

# --- RIGHT COLUMN: RESULTS ---
with col2:
    st.subheader("🤖 AI Analysis Results")
    
    # Generate prompts based on analysis type
    def create_prompt(analysis_type, report_type, language_pref):
        """Medical analysis ke liye specialized prompts banata hai"""
        
        base_context = f"This is a {report_type} medical report. "
        
        language_instruction = {
            "English": "Reply fully in professional English.",
            "Hinglish": "Reply in natural Hinglish (mixed Hindi-English).",
            "Hindi": "Reply in Hindi language.",
            "Match My Input": "Reply in the same language and tone I use. If I write in English → reply in English. If I write in Hinglish → reply in Hinglish."
        }
        
        prompts = {
            "🔍 Simple Explanation": f"""
                {base_context}
                Analyze this medical report and explain in SIMPLE, EASY-TO-UNDERSTAND terms:
                
                1. What tests were done?
                2. What do the numbers mean? (Normal vs Abnormal)
                3. Overall health status
                4. Any areas of concern?
                
                Use simple language as if explaining to someone with no medical background.
                {language_instruction[language_pref]}
            """,
            
            "📊 Detailed Analysis": f"""
                {base_context}
                Provide a COMPREHENSIVE medical analysis:
                
                1. **Test Parameters:** List all tests with values and reference ranges
                2. **Abnormalities:** Highlight out-of-range values with severity (mild/moderate/severe)
                3. **Clinical Significance:** What each abnormal value indicates
                4. **Interconnections:** How different parameters relate to each other
                5. **Further Testing:** Suggest additional tests if needed
                
                {language_instruction[language_pref]}
            """,
            
            "💊 Health Recommendations": f"""
                {base_context}
                Based on this medical report, provide ACTIONABLE health recommendations:
                
                1. **Dietary Suggestions:** Foods to eat and avoid
                2. **Lifestyle Changes:** Exercise, sleep, stress management
                3. **Supplements:** If any deficiencies detected
                4. **Precautions:** Things to monitor or be careful about
                5. **When to See Doctor:** Red flags requiring immediate attention
                
                {language_instruction[language_pref]}
            """,
            
            "📈 Trend Analysis": f"""
                {base_context}
                Analyze health trends and patterns:
                
                1. Identify key health markers
                2. Compare with standard healthy ranges
                3. Predict potential health trajectory if these values continue
                4. Suggest monitoring frequency
                5. Create a simple tracking plan
                
                {language_instruction[language_pref]}
            """,
            
            "🩺 All-in-One Report": f"""
                {base_context}
                Provide a COMPLETE medical report analysis with:
                
                ## 📋 Summary
                - Overall health status in one sentence
                
                ## 🔬 Test Results
                - All parameters with normal/abnormal indicators
                
                ## ⚠️ Key Findings
                - Important abnormalities and their meanings
                
                ## 💡 Simple Explanation
                - What this means for the patient in simple terms
                
                ## 🥗 Lifestyle Recommendations
                - Diet, exercise, and lifestyle changes
                
                ## 🚨 Action Items
                - What to do next (doctor visit, follow-up tests, etc.)
                
                {language_instruction[language_pref]}
            """
        }
        
        return prompts.get(analysis_type, prompts["🔍 Simple Explanation"])
    
    # Analyze button
    if st.button("🔬 Analyze Report", type="primary", use_container_width=True):
        
        # Validation
        if not uploaded_file and not text_input:
            st.warning("⚠️ Please provide either an image or text input!")
        else:
            with st.spinner("🤖 AI is analyzing your report... Please wait..."):
                try:
                    # Create prompt
                    prompt = create_prompt(analysis_type, report_type, language_pref)
                    
                    # Generate response
                    if uploaded_file:
                        # Image + Text prompt
                        img = Image.open(uploaded_file)
                        response = model.generate_content([prompt, img])
                    else:
                        # Text only
                        full_prompt = f"{prompt}\n\nMEDICAL REPORT DATA:\n{text_input}"
                        response = model.generate_content(full_prompt)
                    
                    # Display results
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown("### ✅ Analysis Complete!")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Response text
                    st.markdown("---")
                    st.markdown(response.text)
                    
                    # Metadata
                    st.markdown("---")
                    st.caption(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    if report_name:
                        st.caption(f"📋 Report: {report_name}")
                    st.caption(f"🤖 Model: Gemini 2.0 Flash")
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Analysis",
                        data=response.text,
                        file_name=f"MediView_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {e}")
                    st.info("Please check your API key and internet connection.")

# --- FOOTER SECTION ---
st.markdown("---")
st.markdown("""
<div class="info-box">
    <h4>🎯 How to Use MediView AI:</h4>
    <ol>
        <li>Choose input method (Image upload or Text entry)</li>
        <li>Select analysis type from sidebar</li>
        <li>Upload your medical report or paste the data</li>
        <li>Click "Analyze Report" button</li>
        <li>Get AI-powered insights in simple language!</li>
    </ol>
    <h4>📌 Features:</h4>
    ✅ Supports multiple report types (Blood, Lipid, Thyroid, etc.)<br>
    ✅ Multi-language support (English, Hinglish, Hindi)<br>
    ✅ Different analysis modes (Simple, Detailed, Recommendations)<br>
    ✅ Download analysis reports<br>
    ✅ Privacy-focused (no data storage)
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR FOOTER ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💬 Support & Info")
    st.info("Having trouble or wanna share feedback? Ping your dev — Himanshu Pandey 🚀")
    st.markdown("**Version:** 1.0.2 – MedView AI 💉")
    st.markdown("**Crafted with 🤍, logic & caffeine by Himanshu Pandey**")