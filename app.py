import asyncio
import sys
import os
import warnings
import subprocess

# 🛠️ STARTUP: Ensure Playwright is ready (Crucial for Streamlit Cloud)
def install_playwright():
    try:
        import playwright
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    
    # Check if chromium is installed in the cache
    cache_path = os.path.expanduser("~/.cache/ms-playwright")
    if not os.path.exists(cache_path):
        with st.spinner("First time setup: Installing Browser Engines..."):
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
            subprocess.run([sys.executable, "-m", "playwright", "install-deps"])

# FIX: Force Windows to use the correct Asyncio loop
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass

import streamlit as st
import joblib
import numpy as np
from scraper_test import scrape_amazon_reviews, search_amazon, search_flipkart
from src.preprocess import clean_text
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

# Page Setup
st.set_page_config(page_title="AI Review Validator", layout="wide", page_icon="🛡️")

# Run Playwright install check
install_playwright()

# 1. Load Model
@st.cache_resource
def load_model():
    # Load the saved model and vectorizer
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists in the repo.")

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
    # 0 = Fake (CG), 1 = Real (OR)
    ai_confidence = probs[1] * 100 
    
    # 2. Hybrid Logic Calculations (Heuristics)
    unique_ratio = len(set(words)) / len(words)
    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

    # 3. Final Verdict Decision (AI + Heuristics)
    # Flag as fake if AI says so, OR if it's extremely repetitive, OR weirdly long words
    is_fake = (prediction_index == 0) or (unique_ratio < 0.15) or (avg_word_length > 12)

    # --- DEBUG DASHBOARD ---
    with st.expander("📊 Technical Analysis (Deep Dive)"):
        col1, col2, col3 = st.columns(3)
        col1.metric("AI Real Confidence", f"{ai_confidence:.1f}%")
        col2.metric("Uniqueness Score", f"{unique_ratio:.2f}")
        col3.metric("Avg Word Length", f"{avg_word_length:.1f}")
        
        if prediction_index == 0:
            st.write("🤖 **AI Verdict:** Matches patterns of **Computer-Generated (CG)** reviews.")
        else:
            st.write("🤖 **AI Verdict:** Matches patterns of **Original (OR)** reviews.")

    # DISPLAY VERDICT 
    if is_fake:
        st.error("### 🚩 VERDICT: SUSPICIOUS / FAKE")
        if prediction_index == 1:
            st.warning("⚠️ **Heuristic Override Applied**")
            st.write("The AI suggests this might be 'Real', but our safety checks flagged it for suspicious repetition or structure.")
    else:
        st.success("### ✅ VERDICT: LIKELY REAL")
        st.info(f"**Reason:** Natural Language Patterns | AI Confidence: {ai_confidence:.1f}%")

    # VISUAL EXPLANATION (LIME) 
    st.subheader("🔍 Feature Importance")
    with st.spinner("Analyzing word impact..."):
        explainer = LimeTextExplainer(class_names=['Fake', 'Real'])
        exp = explainer.explain_instance(cleaned, c.predict_proba, num_features=10)
        lime_html = exp.as_html()
        
        # Dark mode support for LIME
        improved_css = """
        <style>
            body, .lime { background-color: #0e1117 !important; color: #ffffff !important; }
            div, p, b { color: #ffffff !important; } 
            text { fill: #ffffff !important; font-size: 12px !important; }
            .lime.label { color: #ffaa00 !important; font-weight: bold !important; }
        </style>
        """
        components.html(improved_css + lime_html, height=400, scrolling=True)

# --- UI LAYOUT TABS ---
tab1, tab2, tab3 = st.tabs(["📝 Manual Input", "🌐 Amazon URL Scraper", "⚖️ Cross-Platform Search"])

# TAB 1: Manual Check
with tab1:
    st.subheader("Analyze a Single Review")
    if 'input_text' not in st.session_state:
        st.session_state['input_text'] = ""

    def clear_text():
        st.session_state['input_text'] = ""

    manual_review = st.text_area("Paste review text here:", value=st.session_state['input_text'], height=150, key="manual_area")

    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("Analyze", key="manual_btn"):
            if manual_review:
                run_analysis(manual_review)
            else:
                st.warning("Please enter text first.")
    with c2:
        st.button("Clear", on_click=clear_text)

# TAB 2: URL Scraper
with tab2:
    st.subheader("🌐 Live Amazon Product Analysis")
    product_url = st.text_input("Paste Amazon Product URL:", key="scraper_url_input", placeholder="https://www.amazon.in/dp/...")

    if st.button("Extract & Analyze", key="url_btn"):
        if product_url:
            with st.spinner("Scraping live reviews (this may take 30s)..."):
                reviews = scrape_amazon_reviews(product_url)
            
            if not reviews:
                st.error("No reviews found. Amazon may be blocking the request or the URL is invalid.")
            else:
                real_count = 0
                for r_text in reviews:
                    cleaned = clean_text(r_text)
                    probs = c.predict_proba([cleaned])[0]
                    if np.argmax(probs) == 1: real_count += 1
                
                real_ratio = real_count / len(reviews)
                ai_rating = real_ratio * 5
                
                st.divider()
                st.header("📊 Product Integrity Report")
                
                col_stars, col_metrics = st.columns([1, 2])
                with col_stars:
                    st.metric("AI Trust Score", f"{ai_rating:.1f} / 5")
                    st.subheader("⭐" * int(round(ai_rating)) if ai_rating >= 0.5 else "🌑")

                with col_metrics:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Scraped", len(reviews))
                    m2.metric("Real", real_count)
                    m3.metric("Suspicious", len(reviews) - real_count)

                st.divider()
                st.subheader("📑 Detailed Breakdown")
                for i, r_text in enumerate(reviews):
                    with st.expander(f"Review #{i+1}"):
                        st.write(f"\"{r_text[:300]}...\"")
                        run_analysis(r_text)
        else:
            st.warning("Please enter a URL.")

# TAB 3: Search
with tab3:
    st.subheader("⚖️ Amazon vs Flipkart Search")
    product_name = st.text_input("Enter Product Name:", placeholder="e.g. iPhone 15 Pro")

    if st.button("Compare Platforms", key="multi_search_btn"):
        if product_name:
            with st.spinner(f"Scraping '{product_name}'..."):
                amz_reviews = search_amazon(product_name, max_reviews=15)
                flp_reviews = search_flipkart(product_name, max_reviews=15)
            
            col_a, col_f = st.columns(2)
            
            with col_a:
                st.subheader("📦 Amazon.in")
                if amz_reviews:
                    r_count = sum(1 for r in amz_reviews if np.argmax(c.predict_proba([clean_text(r)])[0]) == 1)
                    score = (r_count/len(amz_reviews)) * 100
                    st.metric("Integrity", f"{score:.1f}%")
                    st.write(f"**{r_count}** of {len(amz_reviews)} reviews are likely Real.")
                else:
                    st.warning("No Amazon data found.")

            with col_f:
                st.subheader("🛒 Flipkart")
                if flp_reviews:
                    r_count = sum(1 for r in flp_reviews if np.argmax(c.predict_proba([clean_text(r)])[0]) == 1)
                    score = (r_count/len(flp_reviews)) * 100
                    st.metric("Integrity", f"{score:.1f}%")
                    st.write(f"**{r_count}** of {len(flp_reviews)} reviews are likely Real.")
                else:
                    st.warning("No Flipkart data found.")
            
            with st.expander("View Raw Data"):
                st.json({"Amazon": amz_reviews, "Flipkart": flp_reviews})
        else:
            st.warning("Please enter a product name.")
