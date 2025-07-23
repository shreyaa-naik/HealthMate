import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Load dataset
df = pd.read_csv("dataset.csv")

# 2. Strip whitespaces from all cells
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# 3. Extract symptoms as list
symptom_cols = [col for col in df.columns if col.startswith("Symptom")]
df["Symptom_List"] = df[symptom_cols].values.tolist()

# 4. Clean symptom list
df["Symptom_List"] = df["Symptom_List"].apply(
    lambda x: [sym.strip() for sym in x if isinstance(sym, str) and sym.strip()]
)

# 5. Drop rows with no symptoms
df = df[df["Symptom_List"].map(len) > 0]

# 6. Encode symptoms
mlb = MultiLabelBinarizer()
X = mlb.fit_transform(df["Symptom_List"])
y = df["Disease"]

# 7. Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 8. Train
model = RandomForestClassifier()
model.fit(X_train, y_train)

# 9. Evaluate
accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Model accuracy: {accuracy:.2f}")

# 10. Save model and encoder
joblib.dump(model, "disease_model.pkl")
joblib.dump(mlb, "symptom_encoder.pkl")
