
import sys
import os
import streamlit as st  # <--- THIS MUST BE HERE

# 1. Path and Browser Logic
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

@st.cache_resource
def install_browser():
    os.system("playwright install chromium")

install_browser()

# ... rest of your imports (asyncio, joblib, etc.)

# 1. FIX: Correct path addition to find the 'src' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 2. FIX: Install Playwright browser only once
@st.cache_resource
def install_browser():
    os.system("playwright install chromium")

install_browser()
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
    st.subheader("🌐 Amazon Product Integrity Report")
    product_url = st.text_input("Paste Amazon Product URL:", placeholder="https://www.amazon.in/dp/...")

    if st.button("Generate Integrity Report", key="gen_report_btn"):
        if not product_url:
            st.warning("Please provide a valid URL first.")
        else:
            with st.spinner("🕵️ AI is investigating product reviews..."):
                reviews = scrape_amazon_reviews(product_url)
                
                if not reviews:
                    st.error("Could not extract reviews. The product may have no reviews or the scraper was blocked.")
                else:
                    total = len(reviews)
                    genuine_count = 0
                    sabotage_count = 0
                    
                    # Process and categorize reviews
                    for r in reviews:
                        cleaned_r = clean_text(r)
                        if cleaned_r.strip():
                            probs = c.predict_proba([cleaned_r])[0]
                            res = calculate_sabotage_risk(r, probs)
                            if not res["is_sabotage"]:
                                genuine_count += 1
                            else:
                                sabotage_count += 1

                    # --- 1. THE RECALIBRATED RATING ---
                    st.divider()
                    col_rating, col_stats = st.columns([1, 2])
                    
                    with col_rating:
                        # Logic: Genuine ratio determines the new star rating
                        trust_ratio = genuine_count / total
                        final_score = trust_ratio * 5
                        
                        st.metric("Adjusted Trust Rating", f"{final_score:.1f} / 5.0")
                        stars_visual = "⭐" * int(round(final_score)) if final_score >= 0.5 else "🌑"
                        st.subheader(stars_visual)
                        
                        # Quick Verdict Badge
                        if final_score >= 4.0:
                            st.success("✅ HIGH INTEGRITY")
                        elif final_score >= 2.5:
                            st.warning("⚠️ CAUTION: MIXED")
                        else:
                            st.error("🚩 UNTRUSTWORTHY")

                    with col_stats:
                        # Visual Breakdown Metrics
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Analyzed", total)
                        c2.metric("Genuine", genuine_count)
                        c3.metric("Sabotage/Fake", sabotage_count)
                        
                        # Integrity Progress Bar
                        st.write("**Overall Marketplace Authenticity:**")
                        st.progress(trust_ratio)

                    # --- 2. THE DETAILED BREAKDOWN ---
                    st.divider()
                    st.subheader("📑 Top Review Investigations")
                    st.write("Below is a breakdown of the first 5 reviews analyzed for this product.")

with tab3:
    p_name = st.text_input("Product Name:")
    if st.button("Compare Market Integrity"):
        # Your Cross-Platform scraping logic here
        st.info("Comparing Amazon vs Flipkart integrity signatures...")
