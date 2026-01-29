import streamlit as st
import pickle
from src.preprocess import clean_text

st.title("Fake Review Detection System")

with open("model/fake_review_model.pkl", "rb") as f:
    model, vectorizer = pickle.load(f)

review = st.text_area("Enter Review")

if st.button("Check Review"):
    cleaned = clean_text(review)
    vectorized = vectorizer.transform([cleaned])
    result = model.predict(vectorized)
    
    st.success(f"Result: {result[0].upper()}")
    