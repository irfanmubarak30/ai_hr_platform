# RAVDESS: Emotional Intelligence in the HR Platform

The **Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS)** is a core component of the project's vocal analysis capabilities. It provides the foundation for understanding candidate sentiment and behavior during interviews.

## What is RAVDESS?
RAVDESS is a professionally validated multimodal dataset used globally for emotion recognition research. 
- **Scale**: Contains 7,356 recordings.
- **Actors**: Features 24 professional actors (12 male, 12 female).
- **Emotions**: Captures 8 distinct emotional states:
  - 😐 **Neutral**
  - 😌 **Calm**
  - 😊 **Happy**
  - 😢 **Sad**
  - 😠 **Angry**
  - 😨 **Fearful**
  - 🤢 **Disgust**
  - 😲 **Surprised**

## Involvement in this Project

### 1. Voice Analysis Model
The project uses a machine learning model (Multi-Layer Perceptron) trained specifically on the RAVDESS speech dataset.
- **Location**: `voice analysis/voice analysis/model/`
- **Function**: It extracts 390 acoustic features (like MFCCs and Mel Spectrograms) from audio to predict emotional states.
- **Service**: Managed by [voice_analyzer_service.py](file:///c:/Users/irfanmk/Downloads/ai_hr_platform/ai_hr_platform/backend/voice_analyzer_service.py).

### 2. The Interview Audio Pipeline
When a candidate interview call (automated via ElevenLabs) is completed, the following happens:
1. **Syncing**: The platform triggers a sync (manually or via `trigger-now`) to fetch the session data.
2. **Audio Download**: The system retrieves the `recording_url` from ElevenLabs. The `VoiceAnalyzer` downloads this audio to a temporary folder (`tmp/recording_[id].wav`).
3. **RAVDESS Prediction**: The model analyzes the candidate's voice patterns and returns the most likely emotion (e.g., "Happy", "Calm", "Anxious") along with a confidence percentage.

### 3. Behavioral Summary Integration
The RAVDESS results are a key input for the final candidate summary in [ai_evaluator.py](file:///c:/Users/irfanmk/Downloads/ai_hr_platform/ai_hr_platform/backend/ai_evaluator.py):
- **Data Synthesis**: The `generate_behavioral_summary` function receives the **full transcript** and the **voice analysis results**.
- **AI Reasoning**: An LLM (Gemini or Groq) "contextualizes" the words. For example, if a candidate says "I am very excited" but RAVDESS detects "Sad" or "Neutral," the AI might note a lack of genuine enthusiasm.
- **Output Components**:
  - `ravdess result=[emotion]`: Explicitly shows the detected vocal tone.
  - `behavioral summary`: A 1-2 paragraph description of the candidate's demeanor.
  - `overall behaviour score`: A 0-10 score based on leadership, confidence, and clarity.

## What happens if the audio is generated?
If the interview audio is generated (e.g., using a high-quality AI voice or recorded call data), RAVDESS treats it like any other audio. It analyzes the **pitch, tone, and frequency** to find the closest match in its learned emotional categories. This ensures that the behavioral assessment is always grounded in the *audio signal* itself, not just the text.

## Technical Implementation
The pipeline follows these steps:
1. **Extraction**: [feature_extraction.py](file:///c:/Users/irfanmk/Downloads/ai_hr_platform/ai_hr_platform/voice%20analysis/voice%20analysis/feature_extraction.py) processes the raw data into numerical features.
2. **Training**: [train_model.py](file:///c:/Users/irfanmk/Downloads/ai_hr_platform/ai_hr_platform/voice%20analysis/voice%20analysis/train_model.py) builds the neural network with ~62% accuracy.
3. **Inference**: The `VoiceAnalyzer` service predicts emotions for real candidate calls during the sync process in [app.py](file:///c:/Users/irfanmk/Downloads/ai_hr_platform/ai_hr_platform/app.py).

> [!NOTE]
> By using RAVDESS, the platform gains "emotional ears," allowing it to detect if a candidate is calm under pressure or enthusiastic about a role, even if their words are neutral.
