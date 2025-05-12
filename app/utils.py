from transformers import pipeline

emotion_pipeline = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=False
)

def detect_emotion(text: str) -> str:
    result = emotion_pipeline(text)[0]
    return result["label"]
