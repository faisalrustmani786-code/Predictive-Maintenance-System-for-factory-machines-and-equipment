import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiService:
    def __init__(self):
        self.api_key = None
        self.model_name = "gemini-flash-latest"
        self.model = None
        self.last_prompt_sent = ""
        self.load_from_env()
        
    def load_from_env(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        env_model = os.getenv("GEMINI_MODEL")
        if env_model:
            self.model_name = env_model
            
        self.configure(self.api_key)
            
    def configure(self, api_key):
        if api_key and api_key != "your_api_key_here":
            self.api_key = api_key
            genai.configure(api_key=self.api_key)
            # Use requested model or fallback to gemini-flash-latest if not available
            try:
                self.model = genai.GenerativeModel(self.model_name)
            except Exception:
                self.model = genai.GenerativeModel('gemini-flash-latest')
            return True
        return False
        
    def test_connection(self):
        if not self.model:
            return False, "API Key not configured."
        try:
            # Simple test call
            response = self.model.generate_content("Hello")
            if response.text:
                return True, "Connection successful!"
        except Exception as e:
            return False, str(e)
            
    def explain_prediction(self, machine_data, prediction_label, fail_prob, rul, feature_importance):
        """
        Calls Gemini API to get a natural language explanation of the prediction.
        """
        if not self.model:
            return "Gemini API is not configured. Please enter your API key in Settings."
            
        # Format sensor data for prompt
        sensor_text = "\n".join([f"- {k}: {v}" for k, v in machine_data.items()])
        
        # Format feature importance
        imp_text = "\n".join([f"- {f[0]}: {f[1]:.1%} importance" for f in feature_importance[:3]])
        
        prompt = f"""
You are an expert industrial predictive maintenance AI. Analyze the following factory machine state and explain the diagnosis to a maintenance engineer.

Machine Type: {machine_data.get('machine_type', 'Unknown')}
Current Health Diagnosis: {prediction_label}
Failure Probability: {fail_prob:.1f}%
Predicted Remaining Useful Life (RUL): {rul:.1f} hours

Current Sensor Readings:
{sensor_text}

Top Contributing Factors (from ML model):
{imp_text}

Provide a clear, concise explanation containing:
1. A direct statement of the machine's current health.
2. Why this diagnosis was reached, referring to the specific sensor readings and top contributing factors.
3. A recommended action for the maintenance engineer.
4. Keep it under 150 words and professional.
"""
        self.last_prompt_sent = prompt
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Intelligent Local Fallback for Demo Purposes if API Key is blocked (403/429)
            top_feature = feature_importance[0][0].replace("_", " ").title() if feature_importance else "System Sensors"
            
            if prediction_label == "Normal":
                mock_text = f"The {machine_data.get('machine_type', 'machine')} is operating within normal parameters. The primary influential factor is '{top_feature}', which remains completely stable. No immediate maintenance is required. Recommendation: Continue standard continuous monitoring."
            elif prediction_label == "Warning":
                mock_text = f"CAUTION: The {machine_data.get('machine_type', 'machine')} is showing early signs of degradation. Anomalies detected primarily in '{top_feature}'. With an estimated Remaining Useful Life (RUL) of just {rul:.1f} hours, the risk of failure is increasing. Recommendation: Schedule a preventative inspection within the next 48 hours."
            else:
                mock_text = f"CRITICAL ALERT: Imminent failure risk detected for this {machine_data.get('machine_type', 'machine')}. The '{top_feature}' readings are highly anomalous and correlate strongly with historical critical failures. Recommendation: Immediate Action Required! Halt operations and dispatch emergency maintenance crew."
                
            return f"⚠️ [Gemini API Blocked/Offline - Using Local AI Fallback]\n\n{mock_text}"
            
    def get_prompt_used(self):
        return self.last_prompt_sent
        
    def get_api_documentation(self):
        return {
            "API Service": "Google Gemini API via google-generativeai SDK",
            "Model Used": self.model_name,
            "Input": "Structured prompt containing machine state, sensor readings, and ML feature importances.",
            "Output": "Natural-language explanation and maintenance recommendation.",
            "Limitations": "Requires active internet connection and valid API key. May experience latency or rate limits depending on tier."
        }

# Singleton instance
gemini_service = GeminiService()
