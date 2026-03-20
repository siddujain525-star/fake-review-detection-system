import streamlit as st
import pickle
from src.preprocess import clean_text
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

st.set_page_config(page_title="Fake Review Detector", layout="wide")
st.title("🔍 Fake Review Detection + Explainability")

# 1. Load your model and vectorizer
try:
    with open("model/fake_review_model.pkl", "rb") as f:
        model, vectorizer = pickle.load(f)
except Exception as e:
    st.error(f"Error loading model: {e}")

# 2. Create a Pipeline for LIME
c = make_pipeline(vectorizer, model)

# Add a "Clear" button using Session State
if "review_input" not in st.session_state:
    st.session_state.review_input = ""

def clear_text():
    st.session_state.review_input = ""

review = st.text_area("Enter Review to Analyze", value=st.session_state.review_input, height=150, key="review_text")

col1, col2 = st.columns([1, 6])
with col1:
    submit = st.button("Analyze")
with col2:
    st.button("Clear", on_click=clear_text)

if submit:
    if st.session_state.review_text:
        # --- PREDICTION LOGIC ---
        cleaned = clean_text(st.session_state.review_text)
        
        # Get raw prediction
        raw_prediction = model.predict(vectorizer.transform([cleaned]))[0]
        
        # Get Confidence
        probs = c.predict_proba([st.session_state.review_text])[0]
        # Assuming class 0 is OR and class 1 is CG based on alphabetical order
        # We'll calculate confidence based on the winning side
        confidence = max(probs) * 100

        # Mapping: CG (Computer Generated) = FAKE, OR (Original) = REAL
        if raw_prediction == "CG":
            st.error(f"VERDICT: FAKE (Confidence: {confidence:.2f}%)")
        else:
            st.success(f"VERDICT: REAL (Confidence: {confidence:.2f}%)")
            
        # DEBUG: Remove this later, but helps us see if labels are flipped
        st.write(f"DEBUG: Model predicted raw value: {raw_prediction}")

        # --- LIME EXPLAINABILITY SECTION ---
        st.subheader("Why did the AI choose this?")
        
        with st.spinner("Calculating word importance..."):
            # Use the actual internal labels
            explainer = LimeTextExplainer(class_names=['OR', 'CG'])
            exp = explainer.explain_instance(st.session_state.review_text, c.predict_proba, num_features=10)
            
            # CSS for Dark Mode
            lime_html = exp.as_html()
            custom_css = "<style>* { color: white !important; } text { fill: white !important; } .lime.label { color: #ffaa00 !important; font-weight: bold; }</style>"
            components.html(custom_css + lime_html, height=800, scrolling=True)
    else:
        st.warning("Please enter text first.")
