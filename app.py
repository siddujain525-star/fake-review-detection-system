import streamlit as st
import joblib
from src.preprocess import clean_text
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

st.set_page_config(page_title="AI Review Validator", layout="wide")

# 1. Load Model
@st.cache_resource
def load_model():
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}")

st.title("🛡️ AI Review Integrity System")

# 2. Session State for input
if 'input_text' not in st.session_state:
    st.session_state['input_text'] = ""

def clear_text():
    st.session_state['input_text'] = ""

# Input UI
review = st.text_area("Paste review here:", value=st.session_state['input_text'], height=150, key="review_area")

col1, col2 = st.columns([1, 5])
with col1:
    analyze_btn = st.button("Analyze")
with col2:
    st.button("Clear Text", on_click=clear_text)

# --- THE LOGIC BLOCK (Fixed Indentation) ---
if analyze_btn:
    if review:
        # Processing starts exactly 8 spaces in (under the 'if review')
        cleaned = clean_text(review)
        prediction = model.predict(vectorizer.transform([cleaned]))[0]
        probs = c.predict_proba([review])[0]
        class_map = dict(zip(model.classes_, probs))

        # HYBRID LOGIC: Check for repetition (Lexical Diversity)
        words = cleaned.split()
        unique_ratio = len(set(words)) / len(words) if len(words) > 0 else 1
        
        # Check if it should be forced to FAKE
        is_fake = (prediction == "CG") or (unique_ratio < 0.5 and len(words) > 10)

        st.divider()
        if is_fake:
            st.error("### 🚩 VERDICT: FAKE")
            st.write(f"Reasoning: High repetition or bot-like patterns detected.")
        else:
            st.success("### ✅ VERDICT: REAL")
            st.write(f"Reasoning: The text structure appears naturally human.")

        # LIME Section
        # --- FIXED LIME SECTION ---
        st.subheader("Visual Explanation")
        
        # We manually define the mapping to ensure LIME doesn't guess
        # Most models alphabetical: 0 = CG (Fake), 1 = OR (Real)
        map_names = ['Fake (CG)', 'Real (OR)'] 
        
        explainer = LimeTextExplainer(class_names=map_names)
        
        with st.spinner("Generating feature importance..."):
            exp = explainer.explain_instance(
                review, 
                c.predict_proba, 
                num_features=10
            )
            
            # --- CSS to fix Dark Mode & Text Contrast ---
            lime_html = exp.as_html()
            custom_css = """
            <style>
                /* Force all text inside the LIME iframe to be visible */
                .lime { color: white !important; }
                .med { color: white !important; }
                text { fill: white !important; font-size: 12px !important; }
                .lime.label { color: #ffaa00 !important; font-weight: bold; }
                /* Ensure the background of the chart is dark to match Streamlit */
                body { background-color: #0e1117; }
            </style>
            """
            components.html(custom_css + lime_html, height=600, scrolling=True)
