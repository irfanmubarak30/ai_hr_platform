# Speech Emotion Recognition (SER) Project

A complete machine learning pipeline for predicting emotions from voice/audio files using the RAVDESS dataset.

## Project Overview

This project trains a neural network model to recognize 8 different emotions from audio:
- 😠 Angry
- 😌 Calm
- 🤢 Disgust
- 😨 Fearful
- 😊 Happy
- 😐 Neutral
- 😢 Sad
- 😲 Surprised

## Model Performance

- **Test Accuracy**: 62.15%
- **Architecture**: MLP (512 → 256 → 128 → 64 neurons)
- **Training Samples**: 1,152
- **Test Samples**: 288
- **Total Audio Files**: 1,440

### Performance by Emotion

| Emotion | Precision | Recall | F1-Score |
|---------|-----------|--------|----------|
| Angry | 0.80 | 0.74 | 0.77 |
| Calm | 0.77 | 0.71 | 0.74 |
| Happy | 0.80 | 0.41 | 0.54 |
| Surprised | 0.74 | 0.72 | 0.73 |
| Fearful | 0.51 | 0.72 | 0.60 |
| Sad | 0.48 | 0.55 | 0.51 |
| Disgust | 0.61 | 0.50 | 0.55 |
| Neutral | 0.40 | 0.63 | 0.49 |

## Project Structure

```
voice analysis/
├── feature_extraction.py      # Audio feature extraction from .wav files
├── train_model.py             # Model training and evaluation
├── predict.py                 # Emotion prediction from new audio files
├── features_data.pkl          # Extracted features dataset
├── model/
│   ├── emotion_model.pkl      # Trained neural network
│   ├── scaler.pkl             # Feature standardizer
│   └── label_encoder.pkl      # Emotion label encoder
├── emotion_distribution.png   # Dataset emotion distribution plot
├── confusion_matrix.png       # Test set confusion matrix
├── training_loss.png          # Training progress curve
└── archive/
    └── audio_speech_actors_01-24/  # RAVDESS dataset
        ├── Actor_01/
        ├── Actor_02/
        └── ... (24 folders total)
```

## Audio Features Extracted

For each audio file, the following features are extracted:
- **MFCC** (40 coefficients × 2 = 80 features)
- **Chroma STFT** (12 × 2 = 24 features)
- **Mel Spectrogram** (128 × 2 = 256 features)
- **Spectral Contrast** (7 × 2 = 14 features)
- **Tonnetz** (6 × 2 = 12 features)
- **Zero Crossing Rate** (1 × 2 = 2 features)
- **RMS Energy** (1 × 2 = 2 features)

**Total Features**: 390 per audio file

## How to Use

### 1. Extract Features (Already Done ✓)

```bash
python feature_extraction.py
```

This script:
- Scans all audio files in the `archive/` folder
- Extracts 390 features from each audio file
- Saves features to `features_data.pkl`
- Displays emotion distribution

**Status**: ✓ Completed in 337.4 seconds

### 2. Train the Model (Already Done ✓)

```bash
python train_model.py
```

This script:
- Loads pre-extracted features
- Splits data into train/test sets (80/20)
- Standardizes features
- Trains MLP classifier with 4 hidden layers
- Generates evaluation plots and saves the trained model
- Saves model artifacts in `/model` directory

**Status**: ✓ Training accuracy: 62.15%

### 3. Predict Emotion from New Audio

```bash
python predict.py <path_to_audio_file.wav>
```

**Example**:
```bash
python predict.py "archive/audio_speech_actors_01-24/Actor_01/03-01-05-02-01-01-01.wav"
```

**Output**:
```
============================================================
  🎙️  SPEECH EMOTION RECOGNITION — PREDICTION
============================================================

  Audio file: 03-01-05-02-01-01-01.wav

  ┌─────────────────────────────────────────────┐
  │  Predicted Emotion: 😠  ANGRY               │
  │  Confidence:        100.00%                │
  └─────────────────────────────────────────────┘

  Probability Breakdown:
  ─────────────────────────────────────────────
  😠 angry        │██████████████████████████████│ 100.00%
  😌 calm         │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   0.00%
  🤢 disgust      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   0.00%
  ...
```

## Dependencies

- **librosa** - Audio feature extraction
- **numpy** - Numerical operations
- **scikit-learn** - Machine learning models and utilities
- **matplotlib** - Visualization
- **seaborn** - Statistical data visualization
- **joblib** - Model serialization

## Installation

All required packages have been installed. To reinstall or update:

```bash
pip install librosa numpy scikit-learn matplotlib seaborn joblib
```

## Files Generated

### Model Artifacts (in `/model` folder):
- `emotion_model.pkl` - Trained neural network
- `scaler.pkl` - StandardScaler for feature normalization
- `label_encoder.pkl` - Label encoder for emotions

### Visualization Plots:
- `emotion_distribution.png` - Bar chart of dataset emotion distribution
- `confusion_matrix.png` - Heatmap showing model predictions vs actual emotions
- `training_loss.png` - Training and validation curves

## Model Architecture

```
Input (390 features)
         ↓
    Dense (512 neurons) → ReLU
         ↓
    Dense (256 neurons) → ReLU
         ↓
    Dense (128 neurons) → ReLU
         ↓
    Dense (64 neurons) → ReLU
         ↓
    Dense (8 neurons) → Softmax (output emotions)
```

## Training Configuration

- **Optimizer**: Adam
- **Learning Rate**: 0.001 (adaptive)
- **Batch Size**: 32
- **Max Iterations**: 500
- **Regularization (L2)**: 0.001
- **Early Stopping**: Yes (20 epochs without improvement)
- **Validation Split**: 15%

## Next Steps for Improvement

To improve model accuracy (currently 62.15%):

1. **Data Augmentation**:
   - Add time stretching and pitch shifting
   - Add noise and audio effects

2. **Feature Engineering**:
   - Try different MFCC coefficients
   - Experiment with different feature combinations
   - Use temporal features (time-series based)

3. **Model Architecture**:
   - Try deeper networks or different layer sizes
   - Experiment with batch normalization
   - Try dropout for regularization
   - Use Convolutional Neural Networks (CNNs) with spectrograms

4. **Hyperparameter Tuning**:
   - Grid search or random search for optimal parameters
   - Cross-validation during training

5. **Dataset**:
   - Collect more diverse voice samples
   - Balance emotion distribution better
   - Include different speaking styles

## RAVDESS Dataset Format

Filename: `Modality-VocalChannel-Emotion-Intensity-Statement-Repetition-Actor.wav`

Example: `03-01-05-02-01-01-01.wav`
- **03**: Video + Speech (modality)
- **01**: Speech (vocal channel)
- **05**: Angry (emotion)
- **02**: Normal intensity
- **01**: First statement
- **01**: First repetition
- **01**: Actor 01

Emotion Codes:
- 01 = Neutral
- 02 = Calm
- 03 = Happy
- 04 = Sad
- 05 = Angry
- 06 = Fearful
- 07 = Disgust
- 08 = Surprised

## Testing Results ✓

**Test 1**: Actor_01 - Angry emotion
- Predicted: 😠 ANGRY
- Confidence: 100.00%
- Status: ✓ PASS

**Test 2**: Actor_01 - Happy emotion
- Predicted: 😊 HAPPY
- Confidence: 99.44%
- Status: ✓ PASS

## Summary

✓ Project is **100% Complete**
✓ Model is **Trained and Working**
✓ Ready for **Emotion Predictions**

All three main components are fully functional:
1. ✓ Feature extraction pipeline
2. ✓ Model training and evaluation
3. ✓ Prediction system

You can now use this model to predict emotions from any WAV audio file!
