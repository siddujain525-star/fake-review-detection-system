import pickle
from preprocess import clean_text

with open("model/fake_review_model.pkl", "rb") as f:
    model, vectorizer = pickle.load(f)

review = input("Enter review: ")

cleaned = clean_text(review)
vectorized = vectorizer.transform([cleaned])

prediction = model.predict(vectorized)

print("Prediction:", prediction[0])
