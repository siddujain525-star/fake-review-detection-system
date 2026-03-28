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
                # --- TAB 2: Aggregated Analysis with 5-Star Rating ---
with tab2:
    st.subheader("🌐 Live Amazon Product Analysis")
    product_url = st.text_input("Paste an Amazon Product URL here:")

    if st.button("Extract & Analyze Reviews", key="url_btn"):
        if product_url:
            with st.spinner("Scraping and analyzing..."):
                reviews = scrape_amazon_reviews(product_url)
            
            if not reviews:
                st.error("Could not extract reviews.")
            else:
                real_count = 0
                total_reviews = len(reviews)
                
                # Run the model on every review
                for review_text in reviews:
                    cleaned = clean_text(review_text)
                    probs = c.predict_proba([cleaned])[0]
                    if np.argmax(probs) == 1: # 1 is Real
                        real_count += 1
                
                # --- CALCULATE OVERALL AI RATING ---
                # Logic: Percentage of Real Reviews converted to 5-star scale
                real_ratio = real_count / total_reviews
                ai_star_rating = real_ratio * 5
                
                st.divider()
                st.header("🛡️ AI Product Integrity Report")
                
                # Display the Big Star Rating
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("Overall AI Rating", f"{ai_star_rating:.1f} / 5")
                with col2:
                    # Visual Star Display
                    stars = "⭐" * int(round(ai_star_rating))
                    st.subheader(f"Rating: {stars}")

                # --- THE "BUY" VERDICT BASED ON STARS ---
                if ai_star_rating >= 4.0:
                    st.success("### ✅ VERDICT: HIGH INTEGRITY")
                    st.write("Most reviews are genuine. This is a safe choice.")
                elif 2.5 <= ai_star_rating < 4.0:
                    st.warning("### ⚠️ VERDICT: MIXED SIGNALS")
                    st.write("A significant number of reviews look generated. Read carefully.")
                else:
                    st.error("### 🚫 VERDICT: UNTRUSTWORTHY")
                    st.write("Low integrity score. Most reviews appear to be AI-generated/Fake.")

                # Show the breakdown cards
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Analyzed", total_reviews)
                c2.metric("Real Found", real_count)
                c3.metric("Fakes Flagged", total_reviews - real_count)
