"""
feature_extraction.py
---------------------
Extracts audio features from RAVDESS dataset .wav files.
Features extracted:
  - MFCCs (40 coefficients)
  - Chroma (12 features)
  - Mel Spectrogram (128 features)
  - Spectral Contrast (7 features)
  - Tonnetz (6 features)
  - Zero Crossing Rate (1 feature)
  - RMS Energy (1 feature)

RAVDESS filename convention:
  Modality-VocalChannel-Emotion-Intensity-Statement-Repetition-Actor.wav
  Emotion codes: 01=neutral, 02=calm, 03=happy, 04=sad,
                 05=angry, 06=fearful, 07=disgust, 08=surprised
"""

import os
import glob
import numpy as np
import librosa
import pickle
import time


# ── RAVDESS Emotion Mapping ─────────────────────────────────────────────────
EMOTION_MAP = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fearful",
    "07": "disgust",
    "08": "surprised",
}


def extract_features(file_path, sr=22050, duration=3.0):
    """
    Load an audio file and extract a comprehensive feature vector.

    Parameters
    ----------
    file_path : str
        Path to the .wav file.
    sr : int
        Sampling rate for loading audio (default 22050 Hz).
    duration : float
        Maximum duration to load in seconds (default 3.0s).

    Returns
    -------
    np.ndarray
        1-D feature vector (concatenation of all feature means & stds).
    """
    # Load audio (mono, fixed sample rate, fixed duration)
    y, sr = librosa.load(file_path, sr=sr, duration=duration)

    # Pad if the audio is shorter than the target duration
    target_length = int(sr * duration)
    if len(y) < target_length:
        y = np.pad(y, (0, target_length - len(y)), mode="constant")

    # ── Feature extraction ───────────────────────────────────────────────
    # 1. MFCCs (40 coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)

    # 2. Chroma STFT (12 pitch classes)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)

    # 3. Mel Spectrogram (128 mel bands)
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)

    # 4. Spectral Contrast (7 sub-bands)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)

    # 5. Tonnetz (tonal centroid features — 6 dimensions)
    harmonic = librosa.effects.harmonic(y)
    tonnetz = librosa.feature.tonnetz(y=harmonic, sr=sr)

    # 6. Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)

    # 7. RMS Energy
    rms = librosa.feature.rms(y=y)

    # ── Aggregate: mean + std for each feature ───────────────────────────
    features = np.concatenate([
        np.mean(mfccs, axis=1),    np.std(mfccs, axis=1),     # 80
        np.mean(chroma, axis=1),   np.std(chroma, axis=1),    # 24
        np.mean(mel, axis=1),      np.std(mel, axis=1),       # 256
        np.mean(contrast, axis=1), np.std(contrast, axis=1),  # 14
        np.mean(tonnetz, axis=1),  np.std(tonnetz, axis=1),   # 12
        np.mean(zcr, axis=1),      np.std(zcr, axis=1),      # 2
        np.mean(rms, axis=1),      np.std(rms, axis=1),       # 2
    ])

    return features


def parse_emotion_from_filename(filename):
    """
    Extract the emotion label from a RAVDESS filename.

    Parameters
    ----------
    filename : str
        e.g. '03-01-05-02-01-01-01.wav'

    Returns
    -------
    str
        Emotion label, e.g. 'angry'.
    """
    parts = os.path.basename(filename).split("-")
    emotion_code = parts[2]
    return EMOTION_MAP.get(emotion_code, "unknown")


def build_dataset(data_dir, save_path="features_data.pkl"):
    """
    Walk through the RAVDESS directory, extract features
    and labels, and save everything to a pickle file.

    Parameters
    ----------
    data_dir : str
        Root directory of the RAVDESS dataset (containing Actor_XX folders).
    save_path : str
        Path to save the extracted features pickle file.

    Returns
    -------
    tuple
        (X, y) — feature matrix and label array.
    """
    X, y = [], []
    wav_files = glob.glob(os.path.join(data_dir, "Actor_*", "*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files in '{data_dir}'")
    print("=" * 60)

    start_time = time.time()

    for i, file_path in enumerate(wav_files, 1):
        try:
            features = extract_features(file_path)
            emotion = parse_emotion_from_filename(file_path)
            X.append(features)
            y.append(emotion)

            if i % 50 == 0 or i == total:
                elapsed = time.time() - start_time
                rate = i / elapsed
                eta = (total - i) / rate if rate > 0 else 0
                print(
                    f"  [{i:4d}/{total}] "
                    f"Processed: {os.path.basename(file_path):40s} | "
                    f"Emotion: {emotion:10s} | "
                    f"ETA: {eta:.0f}s"
                )
        except Exception as e:
            print(f"  [ERROR] Skipping {file_path}: {e}")

    X = np.array(X)
    y = np.array(y)

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"Feature extraction complete in {elapsed:.1f}s")
    print(f"  Dataset shape: X={X.shape}, y={y.shape}")
    print(f"  Emotion distribution:")
    unique, counts = np.unique(y, return_counts=True)
    for emotion, count in zip(unique, counts):
        print(f"    {emotion:12s}: {count:4d} samples")

    # Save to pickle
    with open(save_path, "wb") as f:
        pickle.dump({"X": X, "y": y}, f)
    print(f"\n  Saved features to '{save_path}'")

    return X, y


if __name__ == "__main__":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "archive")
    SAVE_PATH = os.path.join(os.path.dirname(__file__), "features_data.pkl")

    build_dataset(DATA_DIR, SAVE_PATH)
