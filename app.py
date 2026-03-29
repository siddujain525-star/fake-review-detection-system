from scraper_test import scrape_amazon_reviews, scrape_flipkart_reviews
import streamlit as st
import joblib
import numpy as np
from src.preprocess import clean_text
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

# 1. Page Config
st.set_page_config(page_title="AI Review Analyser", layout="wide")

# 2. Load Model
@st.cache_resource
def load_model():
    # Ensure this matches your filename on GitHub exactly
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists.")

st.title("🛡️ AI Review Analysis System")

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

    # UI Metrics Dashboard
    with st.expander(f"📊 Technical Analysis Metrics", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("AI Real Confidence", f"{ai_confidence:.1f}%")
        col2.metric("Uniqueness Score", f"{unique_ratio:.2f}")
        col3.metric("Avg Word Length", f"{avg_word_length:.1f}")

    if is_fake:
        st.error("### 🚩 VERDICT: FAKE")
        if prediction_index == 1:
            st.warning("⚠️ **Heuristic Override Applied:** High repetition or unusual word length detected.")
    else:
        st.success("### ✅ VERDICT: REAL")

    # 2. Visual Explanation (On-demand to save resources)
    if st.button(f"🔍 Show AI Reasoning (LIME)", key=f"lime_btn_{key_suffix}"):
        with st.spinner("Generating feature importance..."):
            explainer = LimeTextExplainer(class_names=['Fake', 'Real'])
            exp = explainer.explain_instance(cleaned, c.predict_proba, num_features=10)
            
            # CSS to fix dark mode visibility
            improved_css = "<style>body { background-color: #0e1117; color: white; width: 100%; }</style>"
            components.html(improved_css + exp.as_html(), height=450, scrolling=True)

# --- UI LAYOUT TABS ---
tab1, tab2 = st.tabs(["📝 Manual Input Analysis", "🌐 Live Product Review Analysis"])

# TAB 1: Manual Input
with tab1:
    st.subheader("Analyze a Single Review")
    
    if 'input_text' not in st.session_state:
        st.session_state['input_text'] = ""

    def clear_text():
        st.session_state['input_text'] = ""

    manual_review = st.text_area("Paste review here:", value=st.session_state['input_text'], height=150, key="manual_area")

    col_btn1, col_btn2 = st.columns([1, 5])
    analyze_clicked = False
    with col_btn1:
        if st.button("Analyze", key="manual_btn"):
            analyze_clicked = True
    with col_btn2:
        st.button("Clear Text", on_click=clear_text, key="clear_btn")

    # Result appears below columns to prevent "squashed" UI
    if analyze_clicked:
        if manual_review:
            run_analysis(manual_review, key_suffix="manual")
        else:
            st.warning("Please enter a review first!")

# TAB 2: Live Scraper
with tab2:
    st.subheader("🌐 Live Product Review Analysis")
    product_url = st.text_input("Paste Amazon or Flipkart Product URL:", key="scraper_url_input")

    if st.button("Extract & Analyze Reviews", key="url_btn"):
        if product_url:
            with st.spinner("Scraping and detecting source..."):
                # URL Detection Logic
                if "flipkart.com" in product_url or "fkrt.it" in product_url:
                    reviews = scrape_flipkart_reviews(product_url)
                    site_name = "Flipkart"
                elif "amazon" in product_url or "amzn.in" in product_url:
                    reviews = scrape_amazon_reviews(product_url)
                    site_name = "Amazon"
                else:
                    st.error("Platform not supported. Use Amazon or Flipkart.")
                    reviews = None

            if reviews:
                real_count = 0
                total_reviews = len(reviews)
                
                # Batch processing for the Dashboard
                for r_text in reviews:
                    cleaned_r = clean_text(r_text)
                    if np.argmax(c.predict_proba([cleaned_r])[0]) == 1:
                        real_count += 1
                
                ai_star_rating = (real_count / total_reviews) * 5
                
                # Integrity Dashboard
                st.divider()
                st.header(f"🛡️ {site_name} Integrity Report")
                c_stars, c_metrics = st.columns([1, 2])
                with c_stars:
                    st.metric("Overall AI Trust Rating", f"{ai_star_rating:.1f} / 5")
                    stars = "⭐" * int(round(ai_star_rating)) if ai_star_rating > 0 else "🌑"
                    st.subheader(stars)

                with c_metrics:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Reviews", total_reviews)
                    m2.metric("Real Found", real_count)
                    m3.metric("Fakes Flagged", total_reviews - real_count)

                # Summary Verdict
                if ai_star_rating >= 4.0:
                    st.success("### ✅ VERDICT: HIGH INTEGRITY PRODUCT")
                elif ai_star_rating >= 2.5:
                    st.warning("### ⚠️ VERDICT: MIXED SIGNALS / CAUTION")
                else:
                    st.error("### 🚫 VERDICT: UNTRUSTWORTHY / HIGH RISK")

                # Detailed List
                st.divider()
                st.subheader("📑 Detailed Review Breakdown")
                for i, r_text in enumerate(reviews):
                    with st.expander(f"Review {i+1} Details"):
                        st.write(r_text)
                        # Pass unique key suffix for each review in the loop
                        run_analysis(r_text, key_suffix=f"scrape_{i}")
        else:
            st.warning("Please enter a URL first.")
