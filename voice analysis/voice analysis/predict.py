"""
predict.py
----------
Predicts the emotion from a given voice/audio file using the trained model.

Usage:
    python predict.py <path_to_audio_file.wav>

Example:
    python predict.py my_recording.wav
"""

import os
import sys
import numpy as np
import joblib

from feature_extraction import extract_features


# ── Emoji mapping for terminal flair ─────────────────────────────────────────
EMOTION_EMOJI = {
    "neutral":   "😐",
    "calm":      "😌",
    "happy":     "😊",
    "sad":       "😢",
    "angry":     "😠",
    "fearful":   "😨",
    "disgust":   "🤢",
    "surprised": "😲",
}


def load_model(model_dir="model"):
    """
    Load the trained model, scaler, and label encoder.

    Parameters
    ----------
    model_dir : str
        Directory containing model artifacts.

    Returns
    -------
    tuple
        (model, scaler, label_encoder)
    """
    base = os.path.dirname(__file__)
    model_path = os.path.join(base, model_dir, "emotion_model.pkl")
    scaler_path = os.path.join(base, model_dir, "scaler.pkl")
    encoder_path = os.path.join(base, model_dir, "label_encoder.pkl")

    for path, name in [
        (model_path, "Model"),
        (scaler_path, "Scaler"),
        (encoder_path, "Label Encoder"),
    ]:
        if not os.path.exists(path):
            print(f"  [ERROR] {name} not found at '{path}'")
            print("  Please run train_model.py first to train the model.")
            sys.exit(1)

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    le = joblib.load(encoder_path)

    return model, scaler, le


def predict_emotion(audio_path, model_dir="model"):
    """
    Predict the emotion from an audio file.

    Parameters
    ----------
    audio_path : str
        Path to the audio file (.wav).
    model_dir : str
        Directory containing the trained model artifacts.

    Returns
    -------
    dict
        Dictionary with predicted emotion, confidence, and all probabilities.
    """
    # Validate file exists
    if not os.path.exists(audio_path):
        print(f"  [ERROR] Audio file not found: '{audio_path}'")
        sys.exit(1)

    # Load model artifacts
    model, scaler, le = load_model(model_dir)

    # Extract features from the input audio
    features = extract_features(audio_path)
    features = features.reshape(1, -1)

    # Standardize features
    features_scaled = scaler.transform(features)

    # Predict
    prediction = model.predict(features_scaled)
    probabilities = model.predict_proba(features_scaled)[0]

    # Decode label
    predicted_emotion = le.inverse_transform(prediction)[0]
    confidence = np.max(probabilities) * 100

    # Build result
    all_probs = {
        le.inverse_transform([i])[0]: round(prob * 100, 2)
        for i, prob in enumerate(probabilities)
    }
    # Sort by probability descending
    all_probs = dict(sorted(all_probs.items(), key=lambda x: x[1], reverse=True))

    return {
        "predicted_emotion": predicted_emotion,
        "confidence": confidence,
        "all_probabilities": all_probs,
    }


def display_results(result, audio_path):
    """Pretty-print the prediction results."""
    emotion = result["predicted_emotion"]
    confidence = result["confidence"]
    emoji = EMOTION_EMOJI.get(emotion, "🎤")

    print("\n" + "=" * 60)
    print("  🎙️  SPEECH EMOTION RECOGNITION — PREDICTION")
    print("=" * 60)
    print(f"\n  Audio file: {os.path.basename(audio_path)}")
    print(f"\n  ┌─────────────────────────────────────────────┐")
    print(f"  │  Predicted Emotion: {emoji}  {emotion.upper():12s}        │")
    print(f"  │  Confidence:        {confidence:6.2f}%                │")
    print(f"  └─────────────────────────────────────────────┘")

    print(f"\n  Probability Breakdown:")
    print(f"  {'─' * 45}")
    for emo, prob in result["all_probabilities"].items():
        bar_len = int(prob / 100 * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        emo_emoji = EMOTION_EMOJI.get(emo, "")
        print(f"  {emo_emoji} {emo:12s} │{bar}│ {prob:6.2f}%")

    print(f"  {'─' * 45}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n  Usage: python predict.py <path_to_audio_file.wav>")
        print("  Example: python predict.py my_recording.wav\n")
        sys.exit(1)

    audio_file = sys.argv[1]
    result = predict_emotion(audio_file)
    display_results(result, audio_file)
