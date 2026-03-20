import streamlit as st
import pickle
from src.preprocess import clean_text
from lime.lime_text import LimeTextExplainer
import streamlit.components.v1 as components
from sklearn.pipeline import make_pipeline

st.title("🔍 Fake Review Detection + Explainability")

# 1. Load your model and vectorizer
with open("model/fake_review_model.pkl", "rb") as f:
    model, vectorizer = pickle.load(f)

# 2. Create a Pipeline for LIME
# LIME needs to go from Raw Text -> Prediction Probability
c = make_pipeline(vectorizer, model)

review = st.text_area("Enter Review to Analyze", height=150)

if st.button("Analyze Review"):
    if review:
        # Pre-process for the simple result
        cleaned = clean_text(review)
        
        # Get standard prediction
        prediction = model.predict(vectorizer.transform([cleaned]))[0]
        label = "FAKE" if prediction.upper() == "CG" else "REAL"
        
        if label == "FAKE":
            st.error(f"Prediction: {label}")
        else:
            st.success(f"Prediction: {label}")

        # --- LIME EXPLAINABILITY SECTION ---
        st.subheader("Why did the AI choose this?")
        
        with st.spinner("Calculating word importance..."):
            # Initialize explainer
            explainer = LimeTextExplainer(class_names=['Real', 'Fake'])
            
            # Generate explanation
            # We pass the raw 'review' and our pipeline 'c'
            exp = explainer.explain_instance(
                review, 
                c.predict_proba, 
                num_features=10
            )
            
            # Render the LIME HTML in Streamlit
            components.html(exp.as_html(), height=800, scrolling=True)
    else:
        st.warning("Please enter some text first.")upper()}")
    
