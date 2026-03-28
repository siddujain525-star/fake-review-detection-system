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
def run_analysis(review_text):
    cleaned = clean_text(review_text)
    words = cleaned.split()
    
 # --- REUSABLE ANALYSIS FUNCTION WITH DEBUG ---
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

    # 3. Final Verdict Decision
    # We only flag if the AI says it's fake OR if it's extremely repetitive
    is_fake = (prediction_index == 0) or (unique_ratio < 0.15)

    # --- DEBUG DASHBOARD ---
    with st.expander("📊 Technical Analysis (Why is this Fake/Real?)"):
        col1, col2, col3 = st.columns(3)
        col1.metric("AI Real Confidence", f"{ai_confidence:.1f}%")
        col2.metric("Uniqueness Score", f"{unique_ratio:.2f}")
        col3.metric("Avg Word Length", f"{avg_word_length:.1f}")
        
        if prediction_index == 0:
            st.write("🤖 **AI Verdict:** This text patterns match Computer-Generated (CG) reviews.")
        else:
            st.write("🤖 **AI Verdict:** This text patterns match Original (OR) reviews.")

    

    # 1. Get raw probabilities
    probs = c.predict_proba([cleaned])[0]
    prediction_index = np.argmax(probs)
    
    # 2. Hybrid Logic Calculations
    unique_ratio = len(set(words)) / len(words)
    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

    # 3. Final Verdict Decision
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
        # FIXED LINE BELOW
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
        components.html(improved_css + lime_html, height=500, scrolling=True)

# --- UI LAYOUT TABS ---
tab1, tab2 = st.tabs(["📝 Manual Input", "🌐 Live Amazon Scraper"])

with tab1:
    st.subheader("Analyze a Single Review")
    if 'input_text' not in st.session_state:
        st.session_state['input_text'] = ""

    def clear_text():
        st.session_state['input_text'] = ""

    manual_review = st.text_area("Paste review here:", value=st.session_state['input_text'], height=150, key="review_area")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Analyze", key="manual_btn"):
            if manual_review:
                run_analysis(manual_review)
            else:
                st.warning("Please enter a review first!")
    with col2:
        st.button("Clear Text", on_click=clear_text)

# --- TAB 2: Aggregated Analysis ---
with tab2:
    st.subheader("🌐 Live Amazon Product Analysis")
    product_url = st.text_input("Paste an Amazon Product URL here:")

    if st.button("Extract & Analyze Reviews", key="url_btn"):
        if product_url:
            with st.spinner("Scraping and analyzing all reviews..."):
                reviews = scrape_amazon_reviews(product_url)
            
            if not reviews:
                st.error("Could not extract reviews.")
            else:
                # 1. Initialize Counters
                total_reviews = len(reviews)
                real_count = 0
                fake_count = 0
                
                # 2. Run batch analysis (Silent)
                for review_text in reviews:
                    cleaned = clean_text(review_text)
                    probs = c.predict_proba([cleaned])[0]
                    prediction_index = np.argmax(probs)
                    
                    # We use your same logic here
                    if prediction_index == 1: # Real
                        real_count += 1
                    else:
                        fake_count += 1

                # 3. DISPLAY GENERAL ANALYSIS DASHBOARD
                real_percentage = (real_count / total_reviews) * 100
                
                st.divider()
                st.header("📊 Final Product Integrity Report")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Reviews", total_reviews)
                col2.metric("Real Reviews ✅", real_count)
                col3.metric("Generated Reviews 🚩", fake_count)

                # 4. THE "BUY OR NOT" VERDICT
                if real_percentage >= 70:
                    st.success(f"### 🛍️ VERDICT: SAFE TO BUY")
                    st.write(f"**{real_percentage:.1f}%** of reviews appear genuine. This product has high human engagement.")
                elif 40 <= real_percentage < 70:
                    st.warning("### ⚠️ VERDICT: PROCEED WITH CAUTION")
                    st.write(f"Only **{real_percentage:.1f}%** of reviews are verified as real. Some feedback may be manipulated.")
                else:
                    st.error("### 🚫 VERDICT: DO NOT BUY")
                    st.write(f"**{fake_count} out of {total_reviews}** reviews look AI-generated. The rating is likely inflated.")

                st.divider()
                st.subheader("📑 Individual Review Breakdown")
                # Now show the original dropdowns below the summary
                for i, review_text in enumerate(reviews):
                    with st.expander(f"Review {i+1} Details"):
                        run_analysis(review_text)
