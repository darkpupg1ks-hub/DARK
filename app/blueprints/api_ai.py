from flask import Blueprint, request, jsonify, current_app
from ..services.ai_client import AIClient

bp = Blueprint("api_ai", __name__)

@bp.post("/chat")
def chat_api():
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages", [])
    client = AIClient(current_app.config.get("LLM_PROVIDER"), current_app.config.get("OPENAI_API_KEY"))
    try:
        reply = client.chat(messages)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
