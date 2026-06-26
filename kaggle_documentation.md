# 📊 Kaggle Dropout Prevention: Tabular ML Integration & Feature Engineering

This document outlines how to adapt the EduShield AI platform for tabular data competitions, such as the Kaggle **"Predict Students Dropout and Academic Success"** competition. It demonstrates how to replace heuristic risk scores with a trained, production-grade Machine Learning model (e.g., **XGBoost** or **LightGBM**) integrated natively as an MCP tool.

---

## 🛠️ Predictive Machine Learning Pipeline

In a production scenario, the **Risk Assessment Agent** should not rely on static rules. Instead, it queries an MCP tool that wraps a serialized machine learning model.

```
┌─────────────────┐      ┌───────────────┐      ┌────────────────┐      ┌─────────────────────┐
│  Raw Student    ├─────▶│  MCP Server   ├─────▶│ Trained ML     ├─────▶│ Risk Assessment     │
│  Data (Kaggle)  │      │  (mcp_server) │      │ Model (XGBoost)│      │ Agent (ADK LLM)     │
└─────────────────┘      └───────────────┘      └────────────────┘      └─────────────────────┘
                                                      │                            │
                                                      ▼                            ▼
                                                Predictive risk              Explainability & 
                                                metrics (0-100)              actionable plans
```

---

## 📈 Feature Engineering Specification

To achieve top-tier performance on Kaggle dropout datasets, the following feature categories should be engineered and fed into the model:

| Feature Category | Key Tabular Columns | Engineered Features |
| :--- | :--- | :--- |
| **Academic Performance** | Curricular units 1st sem (evaluations, approved, grade), Curricular units 2nd sem | - `CGPA_Trend` (Grade 2nd sem - Grade 1st sem)<br>- `Approval_Rate` (Approved units / Evaluated units) |
| **Engagement** | Attendance rates, class participation logs | - `Low_Attendance_Flag` (Attendance < 75%)<br>- `Engagement_Risk` (Interaction frequency drops) |
| **Financial / Demographics** | Debtor (Yes/No), Tuition fees up to date, Scholarship holder, Gender | - `Financial_Stress_Index` (Debtor + Tuition unpaid)<br>- `Scholarship_Shield` (Scholarship holder acts as safety stabilizer) |
| **Socio-Economic Factors** | Mother's qualification, Father's qualification, Parents' occupation | - `Parent_Higher_Ed` (Flag indicating if parents have college degrees) |

---

## 🤖 Integrating the ML Model as an MCP Tool

Here is how you can deploy your trained XGBoost model within the `mcp_server.py` as an active tool:

```python
import joblib
import pandas as pd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("EduShieldMCP")

# Load the trained model and preprocessing scaler in the server context
try:
    ML_MODEL = joblib.load("models/dropout_xgb_model.pkl")
    SCALER = joblib.load("models/feature_scaler.pkl")
except FileNotFoundError:
    ML_MODEL = None
    SCALER = None

@mcp.tool()
def predict_student_dropout_risk(
    gpa_first_sem: float,
    attendance_rate: float,
    debtor_status: int,
    tuition_fees_paid: int,
    approved_units_ratio: float
) -> dict:
    """
    Evaluate student records using a trained XGBoost ML model to output prediction probabilities.
    """
    if ML_MODEL is None:
        # Fallback heuristic if model is not exported
        heuristic_risk = (10.0 - gpa_first_sem) * 15 + (100 - attendance_rate) * 0.5
        if debtor_status == 1: heuristic_risk += 20
        if tuition_fees_paid == 0: heuristic_risk += 25
        prob = min(max(heuristic_risk / 100.0, 0.05), 0.95)
    else:
        # Construct feature vector
        features = pd.DataFrame([{
            'gpa_1': gpa_first_sem,
            'attendance': attendance_rate,
            'debtor': debtor_status,
            'tuition_paid': tuition_fees_paid,
            'approved_ratio': approved_units_ratio
        }])
        features_scaled = SCALER.transform(features)
        prob = float(ML_MODEL.predict_proba(features_scaled)[0][1]) # Class 1: Dropout
        
    risk_score = int(prob * 100)
    risk_level = "High" if risk_score >= 50 else ("Medium" if risk_score >= 25 else "Low")
    
    return {
        "dropout_probability": prob,
        "dropout_risk_score": risk_score,
        "risk_level": risk_level,
        "top_contributing_factors": [
            "Low unit approval rate" if approved_units_ratio < 0.8 else None,
            "Tuition fee arrears" if tuition_fees_paid == 0 else None,
            "Attendance below 75%" if attendance_rate < 75 else None
        ]
    }
```

---

## 🎯 Evaluation Metrics

In Kaggle student success competitions, the target is multi-class (`Dropout`, `Enrolled`, `Graduate`) or binary (`Dropout` vs `Non-Dropout`). The pipeline is evaluated on:

1. **ROC-AUC (Receiver Operating Characteristic - Area Under Curve):** Measures how well the model distinguishes between dropout risk classes. Essential for tuning probability thresholds.
2. **Macro F1-Score:** The primary leaderboard metric, ensuring balanced accuracy across all three classes (especially crucial given class imbalances where the majority of students graduate).
3. **Recall for Dropout Class:** In real-world institutional settings, high **Recall** for the `Dropout` class is prioritized over high precision. We must capture as many at-risk students as possible (minimizing False Negatives), so intervention agents can proactively engage.
