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
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists.")

st.title("🛡️ AI Review Integrity System")

# --- REUSABLE ANALYSIS FUNCTION ---
# This function holds your ML logic so both manual text and scraped text can use it
def run_analysis(review_text):
    cleaned = clean_text(review_text)
    words = cleaned.split()
    
    # Guard against empty/very short reviews
    if len(words) == 0:
        st.warning("Please enter a valid review with actual words.")
        return

    # 1. Get raw probabilities
   # 1. Get raw probabilities
    probs = c.predict_proba([cleaned])[0]
    prediction_index = np.argmax(probs)
    
    # 2. Hybrid Logic Calculations
    unique_ratio = len(set(words)) / len(words)
    generic_words = [] # Note: add generic words here if you have them!
    generic_count = sum(1 for word in words if word.lower() in generic_words)
    generic_ratio = generic_count / len(words) if len(words) > 0 else 0
    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

    # 3. Final Verdict Decision
    is_fake = (prediction_index == 0) or \
              (unique_ratio < 0.65) or \
              (generic_ratio > 0.35) or \
              (avg_word_length > 6.8)

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

    #  VISUAL EXPLANATION (LIME) 
    with st.spinner("Generating feature importance..."):
        explainer = LimeTextExplainer(class_names=['Fake (CG)', 'Real (OR)'])
        exp = explainer.explain_instance(cleaned, c.predict_proba, num_features=10)
        
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


# --- UI LAYOUT TABS ---
tab1, tab2 = st.tabs(["📝 Manual Input", "🌐 Live Amazon Scraper"])

# TAB 1: Your original manual input
with tab1:
    st.subheader("Analyze a Single Review")
    if 'input_text' not in st.session_state:
        st.session_state['input_text'] = ""

    def clear_text():
        st.session_state['input_text'] = ""

    manual_review = st.text_area("Paste review here:", value=st.session_state['input_text'], height=150, key="review_area")

    col1, col2 = st.columns([1, 5])
    with col1:
        analyze_btn = st.button("Analyze", key="manual_btn")
    with col2:
        st.button("Clear Text", on_click=clear_text)

    if analyze_btn:
        if manual_review:
            run_analysis(manual_review)
        else:
            st.warning("Please enter a review first!")

# TAB 2: The new web scraper integration
with tab2:
    st.subheader("Live Amazon Product Analysis")
    product_url = st.text_input("Paste an Amazon Product URL here:")

    if st.button("Extract & Analyze Reviews", key="url_btn"):
        if product_url:
            with st.spinner("Scraping reviews from Amazon... this might take 5-10 seconds."):
                reviews = scrape_amazon_reviews(product_url)
                
            if not reviews:
                st.error("Could not extract reviews. The URL might be invalid or Amazon blocked the request.")
            else:
                st.success(f"Successfully extracted {len(reviews)} reviews!")
                
                # Loop through scraped reviews and display them in clean dropdown boxes
                for i, review_text in enumerate(reviews):
                    with st.expander(f"Review {i+1}: {review_text[:60]}..."):
                        st.write("**Full Review Text:**")
                        st.write(review_text)
                        st.divider()
                        
                        # Call your machine learning logic for this specific scraped review
                        run_analysis(review_text)
        else:
            st.warning("Please enter a URL first.")
