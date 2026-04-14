import os
import sys
import numpy as np
import joblib
import librosa
import requests
import logging

# Add voice analysis directory to path for feature_extraction
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'voice analysis', 'voice analysis'))
from feature_extraction import extract_features

logger = logging.getLogger(__name__)

class VoiceAnalyzer:
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), '..', 'voice analysis', 'voice analysis')
        self.model_dir = os.path.join(self.base_dir, 'model')
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self._load_model()

    def _load_model(self):
        try:
            model_path = os.path.join(self.model_dir, "emotion_model.pkl")
            scaler_path = os.path.join(self.model_dir, "scaler.pkl")
            encoder_path = os.path.join(self.model_dir, "label_encoder.pkl")

            if all(os.path.exists(p) for p in [model_path, scaler_path, encoder_path]):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                self.label_encoder = joblib.load(encoder_path)
                logger.info("Voice analysis model loaded successfully")
            else:
                logger.error("Voice analysis model artifacts missing")
        except Exception as e:
            logger.error(f"Error loading voice analysis model: {e}")

    def analyze_audio(self, audio_path):
        """Analyzes a local WAV file and returns emotion prediction."""
        if not self.model:
            return None

        try:
            # Extract features
            features = extract_features(audio_path)
            features = features.reshape(1, -1)

            # Standardize
            features_scaled = self.scaler.transform(features)

            # Predict
            prediction = self.model.predict(features_scaled)
            probabilities = self.model.predict_proba(features_scaled)[0]

            # Decode
            emotion = self.label_encoder.inverse_transform(prediction)[0]
            confidence = float(np.max(probabilities))

            return {
                "emotion": emotion,
                "confidence": confidence,
                "probabilities": {
                    self.label_encoder.inverse_transform([i])[0]: float(prob)
                    for i, prob in enumerate(probabilities)
                }
            }
        except Exception as e:
            logger.error(f"Error during voice analysis: {e}")
            return None

    def download_and_analyze(self, recording_url, conversation_id, headers=None):
        """Downloads audio from URL or ElevenLabs API and analyzes it."""
        if not recording_url and not conversation_id:
            return None

        # If no URL but we have a conversation_id, use ElevenLabs direct audio endpoint
        actual_url = recording_url
        if not actual_url and conversation_id:
            from backend.config import config
            actual_url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}/audio"
            if not headers:
                headers = {"xi-api-key": config.ELEVENLABS_API_KEY}

        tmp_path = os.path.join('tmp', f"recording_{conversation_id}.wav")
        os.makedirs('tmp', exist_ok=True)

        try:
            # Download file
            logger.info(f"Downloading audio from {actual_url}...")
            resp = requests.get(actual_url, headers=headers, timeout=60)
            if resp.status_code == 200:
                with open(tmp_path, 'wb') as f:
                    f.write(resp.content)
                
                # Analyze
                result = self.analyze_audio(tmp_path)
                
                # Clean up (keep for debug if needed, but normally remove)
                # os.remove(tmp_path) 
                
                return result
            else:
                logger.error(f"Failed to download recording: Status {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Error downloading/analyzing recording: {e}")
        
        return None

voice_analyzer = VoiceAnalyzer()
