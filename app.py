import sys
import os
# Add the current directory to the path so it can find the 'src' folder
sys.path.append(os.path.dirname(__ignore_file__))
import os
# This command downloads the necessary browser for Playwright to run
os.system("playwright install chromium")import asyncio

import warnings
import joblib
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline
from lime.lime_text import LimeTextExplainer

# Internal imports from your project
from src.preprocess import clean_text
from scraper_test import scrape_amazon_reviews, search_amazon, search_flipkart

# FIX: Force Windows to use the correct Asyncio loop
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass

st.set_page_config(page_title="AI Review Integrity System", layout="wide")

# --- 1. MODEL LOADING ---
@st.cache_resource
def load_model():
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists.")

# --- 2. CORE INNOVATION: WSC ENGINE LOGIC ---
def calculate_sabotage_risk(text, probs):
    """
    Implements the Weighted Sabotage Calculation (WSC).
    Identifies 'Market Redirection' and 'Defamatory Language'.
    """
    text_lower = text.lower()
    
    # Redirection Keywords (Competitor steering)
    redirection_terms = ["better than", "instead of", "buy this", "switch to", "competitor", "rival"]
    redirection_score = sum(1 for term in redirection_terms if term in text_lower)
    
    # Defamatory Keywords (Malicious intent)
    defamatory_terms = ["scam", "fraud", "fake product", "don't buy", "garbage", "trash", "worst"]
    defamatory_score = sum(1 for term in defamatory_terms if term in text_lower)
    
    # Weighted calculation: AI Probability + Sabotage Penalties
    # Index 1 = Real, Index 0 = Fake
    base_confidence = probs[1] 
    penalty = (redirection_score * 0.15) + (defamatory_score * 0.1)
    
    adjusted_score = max(0, base_confidence - penalty)
    
    return {
        "adjusted_score": adjusted_score,
        "redirection_found": redirection_score > 0,
        "defamation_found": defamatory_score > 0,
        "is_sabotage": adjusted_score < 0.5 or (redirection_score + defamatory_score > 2)
    }

# --- 3. REUSABLE ANALYSIS FUNCTION ---
def run_analysis(review_text):
    cleaned = clean_text(review_text)
    words = cleaned.split()
    
    if len(words) == 0:
        st.warning("Please enter a valid review.")
        return

    # 1. AI Base Prediction
    probs = c.predict_proba([cleaned])[0]
    
    # 2. Apply WSC Engine
    wsc_results = calculate_sabotage_risk(cleaned, probs)
    
    # 3. Final Verdict Decision
    is_fake = wsc_results["is_sabotage"] or (np.argmax(probs) == 0)

    # --- TECHNICAL BREAKDOWN ---
    with st.expander("🔍 AI Product Integrity Breakdown"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Base AI Confidence", f"{probs[1]*100:.1f}%")
        col2.metric("Redirection Risk", "High" if wsc_results["redirection_found"] else "Low")
        col3.metric("Defamation Risk", "High" if wsc_results["defamation_found"] else "Low")
        
        if wsc_results["redirection_found"]:
            st.info("🚩 **Market Redirection Detected:** Linguistic patterns suggest steering toward competitors.")
        if wsc_results["defamation_found"]:
            st.info("🚩 **Defamatory Language Detected:** High frequency of hostile/malicious phrasing.")

    # DISPLAY VERDICT 
    if is_fake:
        st.error(f"### 🚩 VERDICT: MALICIOUS / FAKE (Adjusted Trust: {wsc_results['adjusted_score']*100:.1f}%)")
    else:
        st.success(f"### ✅ VERDICT: GENUINE (Adjusted Trust: {wsc_results['adjusted_score']*100:.1f}%)")

    # XAI (LIME) 
    st.subheader("💡 Linguistic Feature Explanation (XAI)")
    explainer = LimeTextExplainer(class_names=['Malicious/Fake', 'Genuine'])
    exp = explainer.explain_instance(cleaned, c.predict_proba, num_features=8)
    components.html(exp.as_html(), height=350, scrolling=True)

# --- 4. STREAMLIT UI LAYOUT ---
st.title("🛡️ AI Product Integrity Dashboard")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 Manual Analysis", "🌐 Amazon URL Scraper", "⚖️ Cross-Platform Search"])

# (Tab 1, 2, and 3 logic remains similar to your original, 
# but calls the updated run_analysis with the WSC integration)

with tab1:
    manual_review = st.text_area("Paste review here:", height=150)
    if st.button("Analyze Intent"):
        if manual_review: run_analysis(manual_review)

with tab2:
    product_url = st.text_input("Amazon URL:")
    if st.button("Generate Integrity Report"):
        with st.spinner("Extracting..."):
            reviews = scrape_amazon_reviews(product_url)
            if reviews:
                total = len(reviews)
                genuine = 0
                for r in reviews:
                    probs = c.predict_proba([clean_text(r)])[0]
                    res = calculate_sabotage_risk(r, probs)
                    if not res["is_sabotage"]: genuine += 1
                
                # Adjusted Star Rating
                final_score = (genuine / total) * 5
                st.metric("Trust-Based Star Rating", f"{final_score:.1f} / 5.0")
                st.write("⭐" * int(round(final_score)))
                
                for i, r in enumerate(reviews[:5]): # Show first 5
                    with st.expander(f"Review {i+1}"):
                        run_analysis(r)

with tab3:
    p_name = st.text_input("Product Name:")
    if st.button("Compare Market Integrity"):
        # Your Cross-Platform scraping logic here
        st.info("Comparing Amazon vs Flipkart integrity signatures...")
