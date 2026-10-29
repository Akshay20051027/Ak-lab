import os
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cloud AI Assistant</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 760px; margin: 35px auto; padding: 0 16px; background: #f5f7fb; }
    h1 { color: #172554; }
    #chat { background: white; border: 1px solid #dbe2ea; border-radius: 10px; padding: 16px; min-height: 260px; }
    .message { margin: 10px 0; padding: 10px 12px; border-radius: 8px; white-space: pre-wrap; }
    .user { background: #dbeafe; } .agent { background: #e5e7eb; }
    form { display: flex; gap: 8px; margin-top: 12px; }
    input { flex: 1; padding: 12px; border: 1px solid #cbd5e1; border-radius: 7px; }
    button { padding: 12px 18px; border: 0; border-radius: 7px; cursor: pointer; background: #1d4ed8; color: white; }
    #status { color: #475569; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>Cloud AI Assistant</h1>
  <p>Ask a question and receive a response from the AI agent.</p>
  <div id="chat" aria-live="polite"></div>
  <form id="chat-form">
    <input id="message" placeholder="Type your question..." autocomplete="off" required>
    <button type="submit">Send</button>
  </form>
  <p id="status"></p>
  <script>
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message');
    const chat = document.getElementById('chat');
    const statusText = document.getElementById('status');
    function addMessage(label, text, className) {
      const div = document.createElement('div');
      div.className = 'message ' + className;
      div.textContent = label + ': ' + text;
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    }
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      addMessage('You', message, 'user');
      input.value = '';
      statusText.textContent = 'Agent is thinking...';
      try {
        const response = await fetch('/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Request failed');
        addMessage('AI Agent', data.reply, 'agent');
        statusText.textContent = '';
      } catch (error) {
        statusText.textContent = 'Error: ' + error.message;
      }
    });
  </script>
</body>
</html>
"""

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not configured.")
    return genai.Client(api_key=api_key)

@app.get("/")
def home():
    return render_template_string(HTML_PAGE)

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Please provide a message."}), 400
    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=(
                "You are a helpful AI assistant for college students. "
                "Answer clearly and in student-friendly language.\n\n" + message
            ),
        )
        reply = response.text or "I could not generate a response. Please try again."
        return jsonify({"reply": reply})
    except Exception:
        app.logger.exception("AI response generation failed")
        return jsonify({"error": "The AI service could not process the request. Check the server logs and API configuration."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
