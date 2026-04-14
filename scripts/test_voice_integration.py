import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.voice_analyzer_service import voice_analyzer
from backend.ai_evaluator import generate_behavioral_summary

def test_full_flow():
    print("=== Testing Voice Analysis & Behavioral Summary Integration ===")
    
    # 1. Select a sample file from archive
    sample_audio = os.path.join("voice analysis", "voice analysis", "archive", "Actor_01", "03-01-05-01-01-01-01.wav")
    if not os.path.exists(sample_audio):
        print(f"Error: Sample audio not found at {sample_audio}")
        return

    print(f"1. Analyzing sample audio: {sample_audio}")
    voice_results = voice_analyzer.analyze_audio(sample_audio)
    
    if not voice_results:
        print("Error: Voice analysis failed")
        return
        
    print(f"   - Detected Emotion: {voice_results['emotion']}")
    print(f"   - Confidence: {voice_results['confidence']:.2f}")

    # 2. Mock a transcript
    mock_transcript = """
Agent: Tell me about a time you had to deal with a difficult teammate.
Candidate: Well, there was this one time where my teammate wasn't meeting his deadlines. It was frustrating because it impacted the whole project's timeline.
Agent: And how did you handle that?
Candidate: I decided to talk to him directly. I asked if there was anything I could do to help, or if there were blockers I wasn't aware of. We ended up redistributing some of the tasks, and he felt much more supported. We finished the project on time.
    """
    
    print("\n2. Generating Comprehensive Behavioral Summary...")
    rich_summary = generate_behavioral_summary(mock_transcript, voice_results)
    
    print("\n=== Resulting Summary ===")
    print(rich_summary)
    print("=========================")

if __name__ == "__main__":
    # Ensure tmp directory exists
    os.makedirs('tmp', exist_ok=True)
    test_full_flow()
