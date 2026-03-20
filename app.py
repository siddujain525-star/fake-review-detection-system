import streamlit as st
import joblib  # Better for Random Forest
from src.preprocess import clean_text
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

st.set_page_config(page_title="AI Review Validator", layout="wide")

# 1. Load Model with Joblib
@st.cache_resource
def load_model():
    # If you used pickle to save, change this back to pickle.load
    return joblib.load("model/fake_review_model.pkl")

try:
    model, vectorizer = load_model()
    c = make_pipeline(vectorizer, model)
except Exception as e:
    st.error(f"Upload your model to GitHub: {e}")

st.title("🛡️ AI Review Integrity System")

# 2. Session State for the Clear Button
if 'input_text' not in st.session_state:
    st.session_state['input_text'] = ""

def clear_text():
    st.session_state['input_text'] = ""

# The text area is linked to session_state
review = st.text_area("Paste review here:", value=st.session_state['input_text'], height=150, key="review_area")

col1, col2 = st.columns([1, 5])
with col1:
    analyze_btn = st.button("Analyze")
with col2:
    st.button("Clear Text", on_click=clear_text)

if analyze_btn and review:
    # --- PROCESSSING ---
    cleaned = clean_text(review)
    prediction = model.predict(vectorizer.transform([cleaned]))[0]
    probs = c.predict_proba([review])[0]
    
    # Map probabilities to classes
    class_map = dict(zip(model.classes_, probs))
    
    # --- DISPLAY RESULT ---
   # --- DISPLAY RESULT ---
    st.divider()
    
    # Dynamically find which keys exist in the map (handles 'CG', 'cg', 'OR', 'or', etc.)
    fake_key = next((k for k in class_map if str(k).upper() == 'CG'), None)
    real_key = next((k for k in class_map if str(k).upper() == 'OR'), None)

    if prediction.upper() == "CG" and fake_key:
        st.error(f"### 🚩 VERDICT: FAKE")
        st.write(f"The AI is **{class_map[fake_key]*100:.1f}%** sure this is machine-generated.")
    elif real_key:
        st.success(f"### ✅ VERDICT: REAL")
        st.write(f"The AI is **{class_map[real_key]*100:.1f}%** sure this is a genuine human review.")
    else:
        # Fallback if the labels are totally different (like 0 and 1)
        st.info(f"### Result: {prediction}")
        st.write(f"Confidence: {max(probs)*100:.1f}%"))

    # --- LIME SECTION ---
    st.subheader("Visual Explanation")
    explainer = LimeTextExplainer(class_names=model.classes_)
    exp = explainer.explain_instance(review, c.predict_proba, num_features=10)
    
    # Dark Mode CSS Fix
    custom_css = """
    <style>
        * { color: white !important; }
        text { fill: white !important; }
        .lime.label { color: #ffaa00 !important; font-weight: bold; }
    </style>
    """
    components.html(custom_css + exp.as_html(), height=600, scrolling=True)

elif analyze_btn and not review:
    st.warning("Please enter a review first!")
