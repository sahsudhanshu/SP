import os
import uvicorn
import gradio as gr
from backend.main import app as fastapi_app

# Seed SQLite database on initial start if not already created
if not os.path.exists("backend/database/riskpulse.db"):
    try:
        from scripts.seed_data import seed
        seed()
    except Exception as e:
        print(f"Warning: seeding database failed: {e}")

try:
    import spaces
    GPU = spaces.GPU
except (ImportError, AttributeError):
    def GPU(func):
        return func

@GPU
def predict_sentiment_gpu(text: str = "TCS reports 12% net profit growth driven by banking technology expansion."):
    """ZeroGPU accelerated sentiment analysis endpoint"""
    try:
        from backend.services.nlp import sentiment_engine
        return sentiment_engine.infer(text)
    except Exception as e:
        return {"sentiment_label": "neutral", "sentiment_score": 0.0, "error": str(e)}

def status_check():
    return (
        "🟢 Status: Operational\n"
        "⚡ Mode: Institutional Risk Engine & Portfolio Stress Lab\n"
        "📡 REST Endpoints: /api/v2/dashboard, /api/health, /api/v2/what-if"
    )

with gr.Blocks(title="RiskPulse AI — Backend Services") as demo:
    gr.Markdown("# 🛡️ RiskPulse AI · Production REST API")
    gr.Markdown(
        "Welcome to the backend service for **RiskPulse AI**.\n\n"
        "### Key REST Endpoints:\n"
        "- `GET /api/health` — Service health & sentiment engine diagnostics\n"
        "- `GET /api/v2/dashboard` — Fused signal intelligence & portfolio book\n"
        "- `POST /api/v2/what-if` — Conditional scenario repricing engine\n"
        "- `POST /api/analyze` — NLP extraction & sentiment inference\n\n"
        "Connect your Next.js Vercel frontend by setting `NEXT_PUBLIC_API_URL` to this Space's URL."
    )
    status_btn = gr.Button("Ping Service Health", variant="primary")
    status_output = gr.Textbox(label="System Status", value=status_check())
    status_btn.click(fn=status_check, outputs=status_output)

    with gr.Accordion("⚡ FinBERT Sentiment Inference (GPU Accelerated)", open=True):
        text_input = gr.Textbox(
            label="Financial Headline / Text",
            value="HDFC Bank reports quarterly credit growth beating consensus estimates."
        )
        infer_btn = gr.Button("Analyze Financial Sentiment", variant="secondary")
        infer_output = gr.JSON(label="FinBERT Output")
        infer_btn.click(fn=predict_sentiment_gpu, inputs=text_input, outputs=infer_output)

# Mount the Gradio interface onto FastAPI
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
