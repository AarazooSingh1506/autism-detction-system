# model/create_model.py
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np
import os

# Create a dummy model for demonstration
model = RandomForestClassifier(n_estimators=100)
X_dummy = np.random.rand(100, 17)  # 17 features
y_dummy = np.random.randint(0, 2, 100)  # binary target
model.fit(X_dummy, y_dummy)

# Create the path to save the model
model_path = os.path.join('model', 'autism_model.pkl')
joblib.dump(model, model_path)
print(f"Model created successfully at {model_path}!")