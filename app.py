import streamlit as st  # MUST BE AT THE TOP
import sys
import os
import asyncio
import warnings
import joblib
import numpy as np

# --- 1. CLOUD ENVIRONMENT SETUP ---
# Correct path addition to find the 'src' folder and scraper
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Install Playwright browser binaries for Streamlit Cloud
@st.cache_resource
def install_browser():
    os.system("playwright install chromium")

install_browser()

# --- 2. ADDITIONAL IMPORTS ---
from src.preprocess import clean_text
from scraper_test import scrape_amazon_reviews, search_amazon, search_flipkart
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

# FIX: Force Windows to use the correct Asyncio loop (if running locally)
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass

st.set_page_config(page_title="AI Review Integrity System", layout="wide")

# --- 3. MODEL LOADING ---
@st.cache_resource
def load_model():
    # Ensure this matches your filename on GitHub exactly
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists.")

# --- 4. CORE INNOVATION: WSC ENGINE LOGIC ---
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
    
    # Logic: Flag as sabotage if adjusted score is low OR keyword density is high
    is_sabotage = (adjusted_score < 0.5) or (redirection_score + defamatory_score > 2)
    
    return {
        "adjusted_score": adjusted_score,
        "redirection_found": redirection_score > 0,
        "defamation_found": defamatory_score > 0,
        "is_sabotage": is_sabotage
    }

# --- 5. REUSABLE ANALYSIS FUNCTION ---
def run_analysis(review_text):
    cleaned = clean_text(review_text)
    words = cleaned.split()
    
    if len(words) == 0:
        st.warning("Please enter a valid review.")
        return

    # AI Base Prediction
    probs = c.predict_proba([cleaned])[0]
    
    # Apply WSC Engine
    wsc_results = calculate_sabotage_risk(cleaned, probs)
    
    # Final Verdict Decision
    is_fake = wsc_results["is_sabotage"] or (np.argmax(probs) == 0)

    # --- TECHNICAL BREAKDOWN ---
    with st.expander("🔍 AI Product Integrity Breakdown"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Base AI Confidence", f"{probs[1]*100:.1f}%")
        col2.metric("Redirection Risk", "High" if wsc_results["redirection_found"] else "Low")
        col3.metric("Defamation Risk", "High" if wsc_results["defamation_found"] else "Low")
        
        if wsc_results["redirection_found"]:
            st.info("🚩 **Market Redirection:** Suggests steering toward competitors.")
        if wsc_results["defamation_found"]:
            st.info("🚩 **Defamatory Language:** Hostile or malicious phrasing detected.")

    # DISPLAY VERDICT 
    if is_fake:
        st.error(f"### 🚩 VERDICT: MALICIOUS / FAKE (Adjusted Trust: {wsc_results['adjusted_score']*100:.1f}%)")
    else:
        st.success(f"### ✅ VERDICT: GENUINE (Adjusted Trust: {wsc_results['adjusted_score']*100:.1f}%)")

    # XAI (LIME) 
    st.subheader("💡 Linguistic Feature Explanation (XAI)")
    with st.spinner("Generating explanation..."):
        explainer = LimeTextExplainer(class_names=['Malicious/Fake', 'Genuine'])
        exp = explainer.explain_instance(cleaned, c.predict_proba, num_features=8)
        components.html(exp.as_html(), height=350, scrolling=True)

# --- 6. STREAMLIT UI LAYOUT ---
st.title("🛡️ AI Product Integrity Dashboard")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 Manual Analysis", "🌐 Amazon URL Scraper", "⚖️ Cross-Platform Search"])

# TAB 1: Manual Check
with tab1:
    st.subheader("Analyze a Single Review")
    manual_review = st.text_area("Paste review here:", height=150)
    if st.button("Analyze Intent"):
        if manual_review:
            run_analysis(manual_review)
        else:
            st.warning("Please enter a review first!")

# TAB 2: Live Amazon Scraper
with tab2:
    st.subheader("🌐 Amazon Product Integrity Report")
    product_url = st.text_input("Paste Amazon Product URL:", placeholder="https://www.amazon.in/dp/...")

    if st.button("Generate Integrity Report"):
        if not product_url:
            st.warning("Please provide a URL.")
        else:
            with st.spinner("🕵️ AI is investigating product reviews..."):
                reviews = scrape_amazon_reviews(product_url)
                
                if not reviews:
                    st.error("Extraction failed. The scraper may be blocked or URL is invalid.")
                else:
                    total = len(reviews)
                    genuine_count = 0
                    sabotage_count = 0
                    
                    for r in reviews:
                        cleaned_r = clean_text(r)
                        if cleaned_r.strip():
                            probs = c.predict_proba([cleaned_r])[0]
                            res = calculate_sabotage_risk(r, probs)
                            if not res["is_sabotage"]:
                                genuine_count += 1
                            else:
                                sabotage_count += 1

                    # Recalibrated Rating Section
                    st.divider()
                    col_rating, col_stats = st.columns([1, 2])
                    
                    with col_rating:
                        trust_ratio = genuine_count / total
                        final_score = trust_ratio * 5
                        st.metric("Adjusted Trust Rating", f"{final_score:.1f} / 5.0")
                        st.subheader("⭐" * int(round(final_score)) if final_score >= 0.5 else "🌑")
                        
                        if final_score >= 4.0: st.success("✅ HIGH INTEGRITY")
                        elif final_score >= 2.5: st.warning("⚠️ CAUTION: MIXED")
                        else: st.error("🚩 UNTRUSTWORTHY")

                    with col_stats:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Analyzed", total)
                        c2.metric("Genuine", genuine_count)
                        c3.metric("Fakes", sabotage_count)
                        st.write("**Overall Marketplace Authenticity:**")
                        st.progress(trust_ratio)

                    st.divider()
                    st.subheader("📑 Top Review Investigations")
                    st.write("Below is a breakdown of the first 5 reviews analyzed for this product.")
                    
                    for i, r_text in enumerate(reviews[:5]):
                        with st.expander(f"Review #{i+1} Investigation Details"):
                            run_analysis(r_text)

# TAB 3: Cross-Platform Search
with tab3:
    st.title("🛡️ Cross-Platform Review Integrity")
    product_name = st.text_input("Enter Product Name (e.g., iPhone 15)")

    if st.button("Run Multi-Site Analysis"):
        with st.spinner(f"Searching Amazon & Flipkart for '{product_name}'..."):
            amz_reviews = search_amazon(product_name, max_reviews=15)
            flp_reviews = search_flipkart(product_name, max_reviews=15)
            
            col_amz, col_flp = st.columns(2)
            
            with col_amz:
                st.header("📦 Amazon India")
                if amz_reviews:
                    real = sum(1 for r in amz_reviews if not calculate_sabotage_risk(r, c.predict_proba([clean_text(r)])[0])["is_sabotage"])
                    score = (real / len(amz_reviews)) * 100
                    st.metric("Integrity Score", f"{score:.1f}%")
                    st.write(f"**{real}** / {len(amz_reviews)} genuine.")
                else:
                    st.warning("No Amazon reviews found.")

            with col_flp:
                st.header("🛒 Flipkart")
                if flp_reviews:
                    real = sum(1 for r in flp_reviews if not calculate_sabotage_risk(r, c.predict_proba([clean_text(r)])[0])["is_sabotage"])
                    score = (real / len(flp_reviews)) * 100
                    st.metric("Integrity Score", f"{score:.1f}%")
                    st.write(f"**{real}** / {len(flp_reviews)} genuine.")
                else:
                    st.warning("No Flipkart reviews found.")
