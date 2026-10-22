# Soya public chat proxy — Azure Functions (Python v2 model).
# Follows Foundry's own "Call soya-260 in code" sample: one conversation per visitor.
# Signs in with the Function App's Managed Identity, so no keys reach the browser.
import json, logging, os, time
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

PROJECT_ENDPOINT = os.environ.get("SOYA_PROJECT_ENDPOINT", "https://copilotfoundary.services.ai.azure.com/api/projects/proj-copilot")
AGENT_NAME = os.environ.get("SOYA_AGENT_NAME", "soya-260")
MAX_PER_HOUR = int(os.environ.get("MAX_MESSAGES_PER_HOUR", "30"))
MAX_CHARS = int(os.environ.get("MAX_INPUT_CHARS", "1500"))

_client = None
def client():
    global _client
    if _client is None:
        project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential(), allow_preview=True)
        _client = project.get_openai_client(agent_name=AGENT_NAME)
    return _client

_hits = {}
def allowed(ip):
    now = time.time()
    recent = [t for t in _hits.get(ip, []) if now - t < 3600]
    if len(recent) >= MAX_PER_HOUR:
        _hits[ip] = recent
        return False
    recent.append(now)
    _hits[ip] = recent
    if len(_hits) > 5000:
        _hits.clear()
    return True

def reply(status, body):
    return func.HttpResponse(json.dumps(body), status_code=status, mimetype="application/json")

@app.route(route="chat", methods=["POST"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    ip = (req.headers.get("x-forwarded-for") or "unknown").split(",")[0].split(":")[0].strip()
    if not allowed(ip):
        return reply(429, {"error": "You've sent a lot of messages. Please try again in an hour."})
    try:
        body = req.get_json()
    except ValueError:
        return reply(400, {"error": "Invalid request."})

    message = str(body.get("message", "")).strip()
    conversation_id = body.get("conversationId")
    if not message:
        return reply(400, {"error": "Please type a question."})
    if len(message) > MAX_CHARS:
        return reply(400, {"error": f"Please keep your question under {MAX_CHARS} characters."})

    try:
        oai = client()
        if not conversation_id:
            conversation_id = oai.conversations.create().id
        response = oai.responses.create(
            conversation=conversation_id,
            input=[{"role": "user", "content": message}],
        )
        text = (response.output_text or "").strip() or "Sorry, I couldn't find an answer."
        return reply(200, {"reply": text, "conversationId": conversation_id})
    except Exception:
        logging.exception("Soya call failed")
        return reply(502, {"error": "Soya is having trouble right now. Please try again shortly."})
