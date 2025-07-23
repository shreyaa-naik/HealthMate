import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

# Helper: Clean symptom names
def clean_symptoms(symptoms):
    return [s.strip().lower().replace("_", " ") for s in symptoms if isinstance(s, str)]

# Load datasets
df = pd.read_csv("cleaned_dataset.csv")
desc_df = pd.read_csv("symptom_Description.csv")
precaution_df = pd.read_csv("symptom_precaution.csv")
severity_df = pd.read_csv("Symptom-severity.csv")

# Normalize columns for matching
desc_df["Symptom"] = desc_df["Symptom"].str.strip().str.lower()
desc_df["Description"] = desc_df["Description"].fillna("No description available.")
precaution_df["Symptom"] = precaution_df["Symptom"].str.strip().str.lower()
severity_df["Symptom"] = severity_df["Symptom"].str.strip().str.lower()

# Extract and process symptom list from dataset
df["Symptom_List"] = df[[col for col in df.columns if col.startswith("Symptom_")]].values.tolist()
df["Symptom_List"] = df["Symptom_List"].apply(clean_symptoms)
df["Symptom_String"] = df["Symptom_List"].apply(lambda x: " ".join(x))

# Vectorize the symptom strings
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["Symptom_String"])
y = df["Disease"].str.strip().str.lower()

# Train the model
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X, y)

# Save the trained model and vectorizer
with open("disease_model.pkl", "wb") as f:
    pickle.dump((model, vectorizer), f)

# Prediction function
def predict_disease(symptom_input):
    # Load model
    with open("disease_model.pkl", "rb") as f:
        model, vectorizer = pickle.load(f)

    # Normalize CSV symptom columns again to be safe
    severity_df["Symptom"] = severity_df["Symptom"].str.strip().str.lower().str.replace("_", " ")
    desc_df["Symptom"] = desc_df["Symptom"].str.strip().str.lower().str.replace("_", " ")
    precaution_df["Symptom"] = precaution_df["Symptom"].str.strip().str.lower().str.replace("_", " ")

    # Clean input symptoms
    cleaned_input = clean_symptoms(symptom_input)
    input_string = " ".join(cleaned_input)
    input_vector = vectorizer.transform([input_string])

    # Make prediction
    prediction = model.predict(input_vector)[0]

    # Compute severity score
    total_severity = 0
    for s in cleaned_input:
        row = severity_df[severity_df["Symptom"] == s]
        if not row.empty:
            total_severity += int(row["weight"].values[0])

    if total_severity == 0:
        suggestion = "No valid symptoms found. Please input correct symptom names."
    elif total_severity <= 5:
        suggestion = "Symptoms seem mild. Maintain hydration and rest."
    elif total_severity <= 10:
        suggestion = "Mild to moderate symptoms. Use home remedies or OTC medicine, and monitor yourself."
    elif total_severity <= 15:
        suggestion = "Symptoms are significant. It is advised to consult a doctor soon."
    else:
        suggestion = "Critical symptoms detected. Seek immediate medical help."

    # Description for each symptom
    symptom_descriptions = []
    for s in cleaned_input:
        row = desc_df[desc_df["Symptom"] == s]
        if not row.empty:
            symptom_descriptions.append(f"{s.title()}: {row['Description'].values[0]}")
    description = "\n".join(symptom_descriptions) if symptom_descriptions else "No symptom description available."

    # Aggregate precautions
    precautions = []
    for s in cleaned_input:
        row = precaution_df[precaution_df["Symptom"] == s]
        if not row.empty:
            precautions.extend(row.iloc[0, 1:].dropna().tolist())
    precautions = list(set(precautions))

    return prediction.title(), suggestion, description, precautions
