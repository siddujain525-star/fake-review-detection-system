from scraper_test import scrape_amazon_reviews
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
    # Ensure this matches your filename on GitHub exactly
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists.")

st.title("🛡️ AI Review Integrity System")

# --- REUSABLE ANALYSIS FUNCTION ---
def run_analysis(review_text):
    cleaned = clean_text(review_text)
    words = cleaned.split()
    
    if len(words) == 0:
        st.warning("Please enter a valid review with actual words.")
        return

    # 1. Get raw probabilities
    probs = c.predict_proba([cleaned])[0]
    prediction_index = np.argmax(probs)
    
    # 2. Hybrid Logic Calculations
    unique_ratio = len(set(words)) / len(words)
    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

    # 3. Final Verdict Decision (CLEANED LOGIC)
    # We trust the AI (prediction_index == 0) 
    # OR we flag if it's extremely repetitive (unique_ratio < 0.20)
    # OR we flag if words are unnaturally long (avg_word_length > 10)
    is_fake = (prediction_index == 0) or (unique_ratio < 0.20) or (avg_word_length > 10)

    # DISPLAY VERDICT 
    if is_fake:
        st.error("### 🚩 VERDICT: FAKE")
        st.info(f"**Reason:** Pattern Mismatch | Uniqueness: {unique_ratio:.2f} | Avg Word Len: {avg_word_length:.1f}")
        
        if prediction_index == 1:
            st.warning("⚠️ **Heuristic Override Applied**")
            st.write("The AI leaned toward 'Real', but safety checks flagged it:")
            if unique_ratio < 0.20: st.write(f"- 🚩 **Low Diversity:** ({unique_ratio:.2f})")
            if avg_word_length > 10: st.write(f"- 🚩 **Unnatural Word Length:** ({avg_word_length:.1f})")
    else:
        st.success("### ✅ VERDICT: REAL")
        st.info(f"**Reason:** Natural Language | AI Confidence: {probs[1]*100:.1f}%")

    # VISUAL EXPLANATION (LIME) 
    st.subheader("🔍 Visual Explanation")
    with st.spinner("Generating feature importance..."):
        explainer = LimeTextExplainer(class_names=['Fake (CG)', 'Real (OR)'])
        exp = explainer.explain_instance(cleaned, c.predict_proba, num_features=
