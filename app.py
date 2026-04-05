from scraper_test import scrape_amazon_reviews
import streamlit as st
import joblib
import numpy as np
import re
from src.preprocess import clean_text
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

st.set_page_config(page_title="AI Review Analyser", layout="wide")

# --- SABOTAGE LOGIC FUNCTION ---
def detect_sabotage(text):
    text_lower = text.lower()
    sabotage_score = 0
    reasons = []
    explanation = ""

    # 1. Competitor Redirection
    competitor_patterns = [r'buy .* instead', r'switch to', r'better than this', r'recommend .* over']
    if any(re.search(p, text_lower) for p in competitor_patterns):
        sabotage_score += 50
        reasons.append("Promoting Competitor")
        explanation += "• **Market Redirection:** The reviewer explicitly suggests a different product, which is a classic sign of competitor-driven sabotage.\n"

    # 2. Defamatory Language
    malicious_terms = ['scam', 'fraud', 'stole', 'sue', 'illegal', 'lawsuit', 'toxic']
    found_terms = [term for term in malicious_terms if term in text_lower]
    if found_terms:
        sabotage_score += 30
        reasons.append("Malicious Keywords")
        explanation += f"• **Extreme Hostility:** Use of legal or high-alert words ({', '.join(found_terms)}) suggests an intent to cause brand damage rather than provide constructive feedback.\n"

    # 3. Structural Aggression
    if len(text) > 50 and text.isupper():
        sabotage_score += 20
        reasons.append("Aggressive Formatting")
        explanation += "• **Formatting Bias:** The use of 'All Caps' combined with negative sentiment is often used in coordinated 'Review Bombing' attacks.\n"

    is_sabotage = sabotage_score >= 50
    return is_sabotage, reasons, sabotage_score, explanation

# --- MODEL LOADING ---
@st.cache_resource
def load_model():
    # Ensure 'model/fake_review_model.pkl' exists in your directory
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Model Load Error: {e}. Ensure 'model/fake_review_model.pkl' exists.")

st.title("🛡️ AI Review Analysis System")

# --- REUSABLE ANALYSIS FUNCTION ---
def run_analysis(review_text):
    cleaned = clean_text(review_text)
    words = cleaned.split()
    
    if len(words) == 0:
        st.warning("Please enter a valid review with actual words.")
        return

    # 1. Get AI raw probabilities
    probs = c.predict_proba([cleaned])[0]
    prediction_index = np.argmax(probs) # 0 = Fake (CG), 1 = Real (OR)
    ai_confidence = probs[1] * 100
    
    # 2. Hybrid Heuristic Calculations
    unique_ratio = len(set(words)) / len(words) if len(words) > 0 else 0
    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

    # 3. Final Verdict Decision (AI + Heuristics)
    is_fake = (prediction_index == 0) or (unique_ratio < 0.15) or (avg_word_length > 10)

    # --- TECHNICAL DASHBOARD ---
    with st.expander("📊 Technical Analysis (Deep Dive)"):
        col1, col2, col3 = st.columns(3)
        col1.metric("AI Real Confidence", f"{ai_confidence:.1f}%")
        col2.metric("Uniqueness Score", f"{unique_ratio:.2f}")
        col3.metric("Avg Word Length", f"{avg_word_length:.1f}")
        
        if prediction_index == 0:
            st.write("🤖 **AI Verdict:** Detected patterns of Computer-Generated (CG) reviews.")
        else:
            st.write("🤖 **AI Verdict:** Detected patterns of Original (OR) reviews.")

    # --- DISPLAY VERDICT & INTENTION ---
    if is_fake:
        st.error("### 🚩 VERDICT: FAKE / UNTRUSTWORTHY")
        
        # New Sabotage Logic Integration
        is_sabotage, reasons, score = detect_sabotage(review_text)
        
        if is_sabotage:
            st.warning(f"⚠️ **INTENTION: MALICIOUS SABOTAGE** (Confidence: {score}%)")
            st.write(f"**Reasoning:** {', '.join(reasons)}")
            st.caption("This review appears to be a targeted attack or competitor promotion.")
        else:
            st.info("ℹ️ **INTENTION: GENERIC SPAM**")
            st.write("This review likely lacks substance or is an automated bot post, but no direct malicious sabotage was detected.")

        if prediction_index == 1:
            st.caption("⚠️ *Heuristic Override:* AI thought this was 'Real', but flagged it for low uniqueness or odd word lengths.")
    else:
        st.success("### ✅ VERDICT: REAL")
        st.info(f"**Reason:** Natural Language Patterns | AI Confidence: {ai_confidence:.1f}%")

    # --- LIME VISUAL EXPLANATION ---
    st.subheader("🔍 Visual Word Importance")
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
tab1, tab2 = st.tabs(["📝 Manual Input Analysis", "🌐 Live Product Review Analysis"])

# --- TAB 1: Manual Check ---
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

# --- TAB 2: Live Scraper Analysis ---
with tab2:
    st.subheader("🌐 Live Product Review Analysis")
    product_url = st.text_input("Paste an Amazon/E-commerce Product URL here:", key="scraper_url_input")

    if st.button("Extract & Analyze Reviews", key="url_btn"):
        if product_url:
            with st.spinner("Scraping and analyzing..."):
                reviews = scrape_amazon_reviews(product_url)
            
            if not reviews:
                st.error("Could not extract reviews. Please try a different URL.")
            else:
                real_count = 0
                total_reviews = len(reviews)
                
                # Preliminary pass to get counts
                for r_text in reviews:
                    cleaned = clean_text(r_text)
                    p = c.predict_proba([cleaned])[0]
                    if np.argmax(p) == 1: real_count += 1
                
                # --- INTEGRITY REPORT ---
                real_ratio = real_count / total_reviews
                ai_star_rating = real_ratio * 5
                
                st.divider()
                st.header("🛡️ AI Product Integrity Report")
                
                c_stars, c_metrics = st.columns([1, 2])
                with c_stars:
                    st.metric("Adjusted AI Rating", f"{ai_star_rating:.1f} / 5")
                    stars_visual = "⭐" * int(round(ai_star_rating))
                    if not stars_visual: stars_visual = "🌑"
                    st.subheader(f"{stars_visual}")

                with c_metrics:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Scanned", total_reviews)
                    m2.metric("Genuine", real_count)
                    m3.metric("Fake/Sabotage", total_reviews - real_count)

                if ai_star_rating >= 4.0:
                    st.success("### ✅ VERDICT: HIGH INTEGRITY")
                elif 2.5 <= ai_star_rating < 4.0:
                    st.warning("### ⚠️ VERDICT: MIXED SIGNALS")
                else:
                    st.error("### 🚫 VERDICT: UNTRUSTWORTHY")

                st.divider()
                st.subheader("📑 Detailed Breakdown per Review")
                for i, r_text in enumerate(reviews):
                    with st.expander(f"Review {i+1} Detail Analysis"):
                        st.write(f"**Original Text:** {r_text}")
                        run_analysis(r_text)
        else:
            st.warning("Please enter a URL first.")
