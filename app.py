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
    ai_confidence = probs[1] * 100
    
    # 2. Hybrid Logic Calculations
    unique_ratio = len(set(words)) / len(words)
    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

    # 3. Final Verdict Decision (AI + Heuristics)
    is_fake = (prediction_index == 0) or (unique_ratio < 0.15) or (avg_word_length > 10)

    # --- DEBUG DASHBOARD ---
    with st.expander("📊 Technical Analysis (Why is this Fake/Real?)"):
        col1, col2, col3 = st.columns(3)
        col1.metric("AI Real Confidence", f"{ai_confidence:.1f}%")
        col2.metric("Uniqueness Score", f"{unique_ratio:.2f}")
        col3.metric("Avg Word Length", f"{avg_word_length:.1f}")
        
        if prediction_index == 0:
            st.write("🤖 **AI Verdict:** This text matches patterns of Computer-Generated (CG) reviews.")
        else:
            st.write("🤖 **AI Verdict:** This text matches patterns of Original (OR) reviews.")

    # DISPLAY VERDICT 
    if is_fake:
        st.error("### 🚩 VERDICT: FAKE")
        if prediction_index == 1:
            st.warning("⚠️ **Heuristic Override Applied**")
            st.write("The AI leaned toward 'Real', but safety checks flagged it for repetition or length.")
    else:
        st.success("### ✅ VERDICT: REAL")
        st.info(f"**Reason:** Natural Language | AI Confidence: {ai_confidence:.1f}%")

    # VISUAL EXPLANATION (LIME) 
    st.subheader("🔍 Visual Explanation")
    with st.spinner("Generating feature importance..."):
        explainer = LimeTextExplainer(class_names=['Fake (CG)', 'Real (OR)'])
        exp = explainer.explain_instance(cleaned, c.predict_proba, num_features=10)
        lime_html = exp.as_html()
        
        improved_css = """
        <style>
            body, .lime { background-color: #0e1117 !important; color: #ffffff !important; }
            div, p, b { color: #ffffff !important; } 
            text { fill: #ffffff !important; font-size: 12px !important; }
            .lime.label { color: #ffaa00 !important; font-weight: bold !important; }
        </style>
        """
        components.html(improved_css + lime_html, height=450, scrolling=True)

# --- UI LAYOUT TABS ---
tab1, tab2 = st.tabs(["📝 Manual Input", "🌐 Live Amazon Scraper"])

# TAB 1: Manual Check
with tab1:
    st.subheader("Analyze a Single Review")
    if 'input_text' not in st.session_state:
        st.session_state['input_text'] = ""

    def clear_text():
        st.session_state['input_text'] = ""

    manual_review = st.text_area("Paste review here:", value=st.session_state['input_text'], height=150, key="manual_area")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Analyze", key="manual_btn"):
            if manual_review:
                run_analysis(manual_review)
            else:
                st.warning("Please enter a review first!")
    with col2:
        st.button("Clear Text", on_click=clear_text, key="clear_btn")

# TAB 2: Live Scraper + 5-Star Rating
with tab2:
    st.subheader("🌐 Universal Product Review Analysis")
    # Added a broader prompt for the user
    product_url = st.text_input("Paste Amazon or Flipkart Product URL:", key="scraper_url_input")

    if st.button("Extract & Analyze Reviews", key="url_btn"):
        if product_url:
            with st.spinner("Detecting site and fetching reviews..."):
                # SITE DETECTION LOGIC
                # --- UPDATED SITE DETECTION ---
if "flipkart.com" in product_url or "fkrt.it" in product_url:
    from scraper_test import scrape_flipkart_reviews
    reviews = scrape_flipkart_reviews(product_url)
    site_name = "Flipkart"
elif "amazon" in product_url or "amzn.in" in product_url:
    reviews = scrape_amazon_reviews(product_url)
    site_name = "Amazon"
else:
    st.error("Platform not supported. Please use an Amazon or Flipkart link.")
    reviews = None

            if reviews:
                st.info(f"Source Detected: **{site_name}** | Reviews Found: {len(reviews)}")
                
                # --- START BATCH ANALYSIS ---
                real_count = 0
                total_reviews = len(reviews)
                
                for review_text in reviews:
                    cleaned = clean_text(review_text)
                    probs = c.predict_proba([cleaned])[0]
                    if np.argmax(probs) == 1: # Real
                        real_count += 1
                
                # --- GENERATE 5-STAR RATING ---
                real_ratio = real_count / total_reviews
                ai_star_rating = real_ratio * 5
                
                st.divider()
                st.header(f"🛡️ {site_name} Integrity Report")
                
                # (Display your Star Rating and Metric Columns as we did before)
                # ...
