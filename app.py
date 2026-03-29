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
def run_analysis(review_text, key_suffix=""):
    cleaned = clean_text(review_text)
    words = cleaned.split()
    
    if len(words) == 0:
        st.warning("Please enter a valid review.")
        return

    # 1. Prediction logic
    probs = c.predict_proba([cleaned])[0]
    prediction_index = np.argmax(probs)
    ai_confidence = probs[1] * 100
    
    unique_ratio = len(set(words)) / len(words)
    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0
    is_fake = (prediction_index == 0) or (unique_ratio < 0.15) or (avg_word_length > 10)

    # UI Metrics Layout
    col1, col2, col3 = st.columns(3)
    col1.metric("AI Real Confidence", f"{ai_confidence:.1f}%")
    col2.metric("Uniqueness Score", f"{unique_ratio:.2f}")
    col3.metric("Avg Word Length", f"{avg_word_length:.1f}")

    if is_fake:
        st.error("### 🚩 VERDICT: FAKE")
    else:
        st.success("### ✅ VERDICT: REAL")

    # 2. Direct Visual Explanation (No Button)
    st.write("🔍 **Visual Reasoning (LIME)**")
    
    # We reduce num_samples for speed when rendering multiple reviews
    explainer = LimeTextExplainer(class_names=['Fake', 'Real'])
    exp = explainer.explain_instance(
        cleaned, 
        c.predict_proba, 
        num_features=6, 
        num_samples=200 # Reduced from 5000 for faster loading
    )
    
    # CSS to force full width and fix dark mode visibility
    improved_css = """
    <style>
        body { background-color: #0e1117; color: white; width: 100%; }
        .lime { width: 100% !important; display: block; }
    </style>
    """
    components.html(improved_css + exp.as_html(), height=350, scrolling=False)

# --- UI LAYOUT TABS ---
tab1, tab2 = st.tabs(["📝 Manual Input", "🌐 Live Amazon Scraper"])

with tab1:
    st.subheader("Analyze a Single Review")
    manual_review = st.text_area("Paste review here:", height=150, key="manual_area")
    
    # Analyze outside of a column to avoid squashed UI
    if st.button("Analyze", key="manual_btn"):
        if manual_review:
            run_analysis(manual_review, key_suffix="manual")

with tab2:
    st.subheader("🌐 Live Amazon Product Analysis")
    product_url = st.text_input("Paste an Amazon Product URL here:", key="scraper_url_input")

    if st.button("Extract & Analyze Reviews", key="url_btn"):
        if product_url:
            with st.spinner("Scraping and analyzing..."):
                reviews = scrape_amazon_reviews(product_url)
            
            if not reviews:
                st.error("Could not extract reviews. Please try a full URL.")
            else:
                real_count = 0
                for r_text in reviews:
                    cleaned_r = clean_text(r_text)
                    if np.argmax(c.predict_proba([cleaned_r])[0]) == 1:
                        real_count += 1
                
                ai_star_rating = (real_count / len(reviews)) * 5
                
                st.divider()
                st.header("🛡️ AI Product Integrity Report")
                c_stars, c_metrics = st.columns([1, 2])
                with c_stars:
                    st.metric("Overall AI Rating", f"{ai_star_rating:.1f} / 5")
                    st.subheader("⭐" * int(round(ai_star_rating)) if ai_star_rating > 0 else "🌑")
                
                with c_metrics:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Reviews", len(reviews))
                    m2.metric("Real", real_count)
                    m3.metric("Fake", len(reviews) - real_count)

                st.divider()
                st.subheader("📑 Detailed Review Breakdown")
                for i, r_text in enumerate(reviews):
                    # Setting expanded=False so LIME only loads when the user opens the box
                    with st.expander(f"Review {i+1} Details", expanded=False):
                        st.write(f"**Text:** {r_text}")
                        run_analysis(r_text, key_suffix=f"scrape_{i}")
