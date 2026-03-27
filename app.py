import streamlit as st
import joblib
import numpy as np
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
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists.")

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

# --- START ANALYSIS ---
if analyze_btn:
    if review:
        cleaned = clean_text(review)
        words = cleaned.split()
        
        # Guard against empty/very short reviews
        if len(words) == 0:
            st.warning("Please enter a valid review with actual words.")
        else:
            # 1. Get raw probabilities
            probs = c.predict_proba([review])[0]
            prediction_index = np.argmax(probs)
            
            # 2. Hybrid Logic Calculations
            unique_ratio = len(set(words)) / len(words)
            generic_words = []
            generic_count = sum(1 for word in words if word.lower() in generic_words)
            generic_ratio = generic_count / len(words)
            avg_word_length = sum(len(word) for word in words) / len(words)

            # 3. Final Verdict Decision
            is_fake = (prediction_index == 0) or \
                      (unique_ratio < 0.65) or \
                      (generic_ratio > 0.35) or \
                      (avg_word_length > 6.8)

            st.divider()

            #  DISPLAY VERDICT 
            if is_fake:
                st.error("### 🚩 VERDICT: FAKE")
                st.info(f"**Reason:** Pattern Mismatch | Uniqueness: {unique_ratio:.2f} | Avg Word Len: {avg_word_length:.1f}")
                
                if prediction_index == 1:
                    st.warning("⚠️ **Heuristic Override Applied**")
                    st.write("The AI model leaned toward 'Real', but our safety checks flagged it:")
                    if unique_ratio < 0.65: st.write(f"- 🚩 **Low Diversity:** ({unique_ratio:.2f})")
                    if generic_ratio > 0.35: st.write(f"- 🚩 **High Generic Content:** ({generic_ratio:.2f})")
                    if avg_word_length > 6.8: st.write(f"- 🚩 **Unnatural Word Length:** ({avg_word_length:.1f})")
            else:
                st.success("### ✅ VERDICT: REAL")
                st.info(f"**Reason:** Natural Language | AI Confidence: {probs[1]*100:.1f}%")

            #  VISUAL EXPLANATION (LIME) local interpretable mobel agnostic explanation )
            st.subheader("🔍 Visual Explanation")
            with st.spinner("Generating feature importance..."):
                explainer = LimeTextExplainer(class_names=['Fake (CG)', 'Real (OR)'])
                exp = explainer.explain_instance(review, c.predict_proba, num_features=10)
                lime_html = exp.as_html()
                
                # DARK THEME VISIBILITY FIX
                improved_css = """
                <style>
                    body, .lime { background-color: #0e1117 !important; color: #ffffff !important; }
                    div, p, b { color: #ffffff !important; } 
                    text { fill: #ffffff !important; font-size: 12px !important; }
                    .lime.label { color: #ffaa00 !important; font-weight: bold !important; }
                </style>
                """
                components.html(improved_css + lime_html, height=500, scrolling=True)
    else:
        st.warning("Please enter a review first!")
