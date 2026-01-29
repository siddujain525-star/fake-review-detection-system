import os
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
from preprocess import clean_text

# Create model folder if it does not exist
os.makedirs("model", exist_ok=True)

# Load dataset
data = pd.read_csv("data/reviews.csv")

data['cleaned_review'] = data['review'].apply(clean_text)

X = data['cleaned_review']
y = data['label']

vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42
)

model = MultinomialNB()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

# Save model
with open("model/fake_review_model.pkl", "wb") as f:
    pickle.dump((model, vectorizer), f)

print("Model saved successfully!")
