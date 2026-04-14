"""
train_model.py
--------------
Trains a Speech Emotion Recognition (SER) model on the RAVDESS dataset.

Pipeline:
  1. Load pre-extracted features (or extract them if not found)
  2. Encode labels
  3. Split into train/test sets
  4. Standardize features
  5. Train an MLP Classifier
  6. Evaluate with classification report & confusion matrix
  7. Save the trained model, scaler, and label encoder
"""

import os
import pickle
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving plots
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)
import joblib


def load_features(features_path):
    """Load features from pickle file."""
    with open(features_path, "rb") as f:
        data = pickle.load(f)
    return data["X"], data["y"]


def plot_confusion_matrix(y_true, y_pred, labels, save_path="confusion_matrix.png"):
    """
    Plot and save a styled confusion matrix.
    """
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_percent = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis] * 100

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        cm_percent,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        xticklabels=labels,
        yticklabels=labels,
        linewidths=0.5,
        linecolor="gray",
        cbar_kws={"label": "Percentage (%)"},
        ax=ax,
    )
    ax.set_xlabel("Predicted Emotion", fontsize=13, fontweight="bold")
    ax.set_ylabel("True Emotion", fontsize=13, fontweight="bold")
    ax.set_title("Emotion Recognition — Confusion Matrix", fontsize=15, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"  Confusion matrix saved to '{save_path}'")
    plt.close()


def plot_emotion_distribution(y, save_path="emotion_distribution.png"):
    """
    Plot and save the emotion distribution in the dataset.
    """
    unique, counts = np.unique(y, return_counts=True)
    colors = sns.color_palette("viridis", len(unique))

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(unique, counts, color=colors, edgecolor="white", linewidth=0.8)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            str(count),
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11,
        )

    ax.set_xlabel("Emotion", fontsize=13, fontweight="bold")
    ax.set_ylabel("Number of Samples", fontsize=13, fontweight="bold")
    ax.set_title("RAVDESS Dataset — Emotion Distribution", fontsize=15, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"  Emotion distribution plot saved to '{save_path}'")
    plt.close()


def train_model(features_path="features_data.pkl", model_dir="model"):
    """
    Full training pipeline.

    Parameters
    ----------
    features_path : str
        Path to the pickled features file.
    model_dir : str
        Directory to save the trained model artifacts.
    """
    # ── 1. Load features ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SPEECH EMOTION RECOGNITION — MODEL TRAINING")
    print("=" * 60)

    if not os.path.exists(features_path):
        print(f"\n  Features file '{features_path}' not found.")
        print("  Running feature extraction first...\n")
        from feature_extraction import build_dataset

        data_dir = os.path.join(os.path.dirname(__file__), "archive")
        build_dataset(data_dir, features_path)

    print(f"\n  Loading features from '{features_path}'...")
    X, y = load_features(features_path)
    print(f"  Loaded {X.shape[0]} samples with {X.shape[1]} features each")

    # ── 2. Encode labels ─────────────────────────────────────────────────
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    print(f"  Classes: {list(le.classes_)}")

    # ── 3. Plot emotion distribution ─────────────────────────────────────
    base_dir = os.path.dirname(__file__)
    plot_emotion_distribution(
        y, save_path=os.path.join(base_dir, "emotion_distribution.png")
    )

    # ── 4. Train/Test split ──────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    print(f"\n  Train set: {X_train.shape[0]} samples")
    print(f"  Test set:  {X_test.shape[0]} samples")

    # ── 5. Standardize features ──────────────────────────────────────────
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # ── 6. Train MLP Classifier ──────────────────────────────────────────
    print("\n  Training MLP Classifier...")
    print("  Architecture: (512) → (256) → (128) → (64)")
    print("  This may take a few minutes...\n")

    mlp = MLPClassifier(
        hidden_layer_sizes=(512, 256, 128, 64),
        activation="relu",
        solver="adam",
        alpha=0.001,              # L2 regularization
        batch_size=32,
        learning_rate="adaptive",
        learning_rate_init=0.001,
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        random_state=42,
        verbose=True,
    )

    mlp.fit(X_train, y_train)

    # ── 7. Evaluate ──────────────────────────────────────────────────────
    y_pred = mlp.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print("\n" + "=" * 60)
    print(f"  TEST ACCURACY: {accuracy * 100:.2f}%")
    print("=" * 60)

    print("\n  Classification Report:")
    print(
        classification_report(
            y_test, y_pred, target_names=le.classes_, zero_division=0
        )
    )

    # Confusion matrix
    plot_confusion_matrix(
        le.inverse_transform(y_test),
        le.inverse_transform(y_pred),
        labels=list(le.classes_),
        save_path=os.path.join(base_dir, "confusion_matrix.png"),
    )

    # ── 8. Plot training loss curve ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(mlp.loss_curve_, color="#e74c3c", linewidth=2, label="Training Loss")
    if hasattr(mlp, "validation_scores_") and mlp.validation_scores_:
        ax2 = ax.twinx()
        ax2.plot(
            mlp.validation_scores_,
            color="#2ecc71",
            linewidth=2,
            label="Validation Accuracy",
        )
        ax2.set_ylabel("Validation Accuracy", fontsize=12, fontweight="bold")
        ax2.legend(loc="center right")
    ax.set_xlabel("Iteration", fontsize=12, fontweight="bold")
    ax.set_ylabel("Loss", fontsize=12, fontweight="bold")
    ax.set_title("Training Progress", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    ax.spines["top"].set_visible(False)
    plt.tight_layout()
    loss_path = os.path.join(base_dir, "training_loss.png")
    plt.savefig(loss_path, dpi=150)
    print(f"  Training loss curve saved to '{loss_path}'")
    plt.close()

    # ── 9. Save model artifacts ──────────────────────────────────────────
    os.makedirs(os.path.join(base_dir, model_dir), exist_ok=True)

    model_path = os.path.join(base_dir, model_dir, "emotion_model.pkl")
    scaler_path = os.path.join(base_dir, model_dir, "scaler.pkl")
    encoder_path = os.path.join(base_dir, model_dir, "label_encoder.pkl")

    joblib.dump(mlp, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(le, encoder_path)

    print(f"\n  Model saved to:          '{model_path}'")
    print(f"  Scaler saved to:         '{scaler_path}'")
    print(f"  Label encoder saved to:  '{encoder_path}'")
    print("\n" + "=" * 60)
    print("  Training complete! Use predict.py to classify new audio.")
    print("=" * 60 + "\n")

    return mlp, scaler, le


if __name__ == "__main__":
    base = os.path.dirname(__file__)
    features_path = os.path.join(base, "features_data.pkl")
    train_model(features_path=features_path, model_dir="model")
