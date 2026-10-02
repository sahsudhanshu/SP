"""Optional one-time download. Subsequent backend starts use only local files."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HOME',str(ROOT/'.models'))
from transformers import AutoTokenizer,AutoModelForSequenceClassification
name=os.getenv('MODEL_NAME','ProsusAI/finbert')
AutoTokenizer.from_pretrained(name)
AutoModelForSequenceClassification.from_pretrained(name)
print('FinBERT cached locally. Start backend with SENTIMENT_MODE=auto.')
