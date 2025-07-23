import pandas as pd
import numpy as np
import re

# Load dataset
df = pd.read_csv("dataset.csv")

# 1. Strip whitespace from column names
df.columns = df.columns.str.strip()

# 2. Clean every cell (symptoms + diseases)
def clean_text(val):
    if isinstance(val, str):
        val = val.strip()
        val = val.lower()  # optional: remove this line if you want title case
        val = re.sub(r'[_\s]+', '_', val)  # unify underscores and multiple spaces
        val = val.replace(",","")  # remove stray commas
        val = val.replace(".", "")  # remove stray periods
        val = val.replace("-", "_")  # unify hyphens
        return val
    return val

# Apply to entire DataFrame
df = df.applymap(clean_text)

# 3. Replace blanks with NaN
df.replace("", np.nan, inplace=True)

# 4. Drop fully empty rows
df.dropna(how="all", inplace=True)

# 5. Reset index
df.reset_index(drop=True, inplace=True)

# 6. Save cleaned version
df.to_csv("cleaned_dataset.csv", index=False)

print("✅ All symptom and disease names cleaned and saved as cleaned_dataset.csv")
