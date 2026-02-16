from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import requests
import os
import json
import re
import uuid
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# Ollama configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "192"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.6"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
CHAT_HISTORY_MESSAGES = int(os.getenv("CHAT_HISTORY_MESSAGES", "6"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "700"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
RAG_AUTO_INGEST_MIN_CHARS = int(os.getenv("RAG_AUTO_INGEST_MIN_CHARS", "600"))
RAG_DB_PATH = os.getenv("RAG_DB_PATH", "/tmp/rag.db")
WEB_LOOKUP_TOP_K = int(os.getenv("WEB_LOOKUP_TOP_K", "5"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")

HTTP_SESSION = requests.Session()

# System prompt for general AI assistant
SYSTEM_PROMPT = """You are a knowledgeable and helpful AI assistant. You can discuss any topic including:
- Technology, programming, and software development
- Science, mathematics, and engineering
- Business, finance, and economics
- Arts, literature, and culture
- History, geography, and current events
- Health, fitness, and wellness
- And much more

Provide clear, accurate, and helpful responses. Use examples when appropriate.
Be conversational and friendly. If you're not sure about something, say so.
Default to concise answers unless the user asks for deep detail.
Keep default answers under 120 words and use short bullet points when possible."""


def tokenize(text):
    return set(re.findall(r"[a-zA-Z0-9_]{3,}", text.lower()))


def chunk_text(text, chunk_size=RAG_CHUNK_SIZE, overlap=RAG_CHUNK_OVERLAP):
    if not text:
        return []

    chunks = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(text), step):
        part = text[start : start + chunk_size].strip()
        if part:
            chunks.append(part)
        if start + chunk_size >= len(text):
            break
    return chunks


def get_db_connection():
    return sqlite3.connect(RAG_DB_PATH)


def init_rag_db():
    db_dir = os.path.dirname(RAG_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                tokens TEXT NOT NULL
            )
            """
        )


def rag_counts():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rag_chunks")
        chunk_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT filename) FROM rag_chunks")
        document_count = cursor.fetchone()[0]

    return document_count, chunk_count


def rag_filenames():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT filename FROM rag_chunks ORDER BY filename")
        return [row[0] for row in cursor.fetchall()]


def add_document_chunks(filename, content):
    chunks = chunk_text(content)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for index, part in enumerate(chunks):
            cursor.execute(
                """
                INSERT INTO rag_chunks (id, filename, chunk_index, content, tokens)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    filename,
                    index,
                    part,
                    json.dumps(sorted(tokenize(part))),
                ),
            )
        conn.commit()
    return len(chunks)


def retrieve_context(query, top_k=RAG_TOP_K):
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, chunk_index, content, tokens FROM rag_chunks")
        rows = cursor.fetchall()

    if not rows:
        return []

    ranked = []
    for filename, chunk_index, content, tokens_json in rows:
        doc_tokens = set(json.loads(tokens_json))
        overlap = len(query_tokens.intersection(doc_tokens))
        if overlap > 0:
            ranked.append(
                (
                    overlap,
                    {
                        "filename": filename,
                        "index": chunk_index,
                        "content": content,
                    },
                )
            )

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in ranked[:top_k]]


def resolve_model(selected_model):
    if isinstance(selected_model, str) and selected_model.strip():
        return selected_model.strip()
    return OLLAMA_MODEL


def should_auto_ingest(message):
    if not isinstance(message, str):
        return False

    text = message.strip()
    if not text:
        return False

    line_count = text.count("\n") + 1
    question_marks = text.count("?")
    looks_long = len(text) >= RAG_AUTO_INGEST_MIN_CHARS or line_count >= 12
    looks_like_question = question_marks >= 2
    return looks_long and not looks_like_question


def ingest_pasted_document(message):
    document_count, _ = rag_counts()
    filename = f"chat-paste-{document_count + 1}.txt"
    chunks_added = add_document_chunks(filename, message)
    return filename, chunks_added


def web_lookup_configured():
    return bool(GOOGLE_API_KEY and GOOGLE_CSE_ID)


def fetch_google_results(query, top_k=WEB_LOOKUP_TOP_K):
    if not web_lookup_configured():
        return [], "not_configured"

    try:
        response = HTTP_SESSION.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CSE_ID,
                "q": query,
                "num": max(1, min(top_k, 10)),
            },
            timeout=(5, 12),
        )

        if not response.ok:
            app.logger.error(f"Google lookup failed: {response.status_code} {response.text}")
            return [], "lookup_failed"

        items = response.json().get("items", [])
        results = []
        for item in items:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            if title or snippet or link:
                results.append({"title": title, "snippet": snippet, "link": link})

        return results, None
    except requests.RequestException as exc:
        app.logger.error(f"Google lookup request error: {exc}")
        return [], "lookup_failed"


def build_system_prompt(rag_enabled, user_message, web_enabled=False, web_results=None):
    prompt = SYSTEM_PROMPT

    if web_enabled and web_results:
        web_blocks = []
        for index, result in enumerate(web_results, start=1):
            web_blocks.append(
                f"[web-{index}] {result.get('title', '')}\n"
                f"Snippet: {result.get('snippet', '')}\n"
                f"URL: {result.get('link', '')}"
            )

        prompt += (
            "\n\nWEB LOOKUP MODE: Use the following Google search snippets as fresh context. "
            "Prefer these sources for time-sensitive facts and mention URLs when useful.\n\n"
            + "\n\n".join(web_blocks)
        )

    if not rag_enabled:
        return prompt

    matches = retrieve_context(user_message)
    if not matches:
        return prompt + "\n\nRAG MODE: No matching document context found for this question."

    context_blocks = []
    for match in matches:
        context_blocks.append(
            f"[{match['filename']}#{match['index']}]\n{match['content']}"
        )

    return (
        prompt
        + "\n\nRAG MODE: Use only the following document context when relevant. "
        + "If context is insufficient, clearly say so.\n\n"
        + "\n\n".join(context_blocks)
    )


def build_messages(
    user_message,
    conversation_history,
    rag_enabled=False,
    web_enabled=False,
    web_results=None,
):
    bounded_history = conversation_history[-CHAT_HISTORY_MESSAGES:]
    messages = [
        {
            "role": "system",
            "content": build_system_prompt(
                rag_enabled, user_message, web_enabled, web_results
            ),
        }
    ]

    for msg in bounded_history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages


def ollama_is_ready():
    try:
        response = HTTP_SESSION.get(f"{OLLAMA_URL}/api/tags", timeout=(3, 5))
        return response.ok
    except requests.RequestException:
        return False


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


@app.route("/api/models", methods=["GET"])
def models():
    try:
        response = HTTP_SESSION.get(f"{OLLAMA_URL}/api/tags", timeout=(3, 8))
        if not response.ok:
            return jsonify({"models": [OLLAMA_MODEL], "default": OLLAMA_MODEL})

        items = response.json().get("models", [])
        names = [item.get("name") for item in items if item.get("name")]
        if OLLAMA_MODEL not in names:
            names.insert(0, OLLAMA_MODEL)

        return jsonify({"models": names, "default": OLLAMA_MODEL})
    except requests.RequestException:
        return jsonify({"models": [OLLAMA_MODEL], "default": OLLAMA_MODEL})


@app.route("/api/web/status", methods=["GET"])
def web_status():
    return jsonify({"configured": web_lookup_configured(), "provider": "google-cse"})


@app.route("/api/rag/upload", methods=["POST"])
def rag_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file provided"}), 400

    filename = file.filename
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    allowed = {"txt", "md", "csv", "log", "json", "yaml", "yml"}
    if extension not in allowed:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Unsupported file type. Use txt, md, csv, log, json, yaml, or yml.",
                }
            ),
            400,
        )

    try:
        content = file.read().decode("utf-8", errors="ignore")
        if not content.strip():
            return jsonify({"success": False, "error": "File is empty"}), 400

        chunks_added = add_document_chunks(filename, content)
        return jsonify(
            {
                "success": True,
                "filename": filename,
                "chunks_added": chunks_added,
                "total_chunks": rag_counts()[1],
            }
        )
    except Exception as exc:
        app.logger.error(f"RAG upload error: {exc}")
        return jsonify({"success": False, "error": "Failed to process file"}), 500


@app.route("/api/rag/status", methods=["GET"])
def rag_status():
    filenames = rag_filenames()
    document_count, chunk_count = rag_counts()
    return jsonify(
        {
            "success": True,
            "documents": filenames,
            "document_count": document_count,
            "chunk_count": chunk_count,
        }
    )


@app.route("/api/rag/clear", methods=["POST"])
def rag_clear():
    with get_db_connection() as conn:
        conn.execute("DELETE FROM rag_chunks")
        conn.commit()
    return jsonify({"success": True, "message": "RAG knowledge base cleared"})


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data["message"]
        conversation_history = data.get("history", [])
        rag_enabled = bool(data.get("rag_enabled", False))
        web_enabled = bool(data.get("web_enabled", False))
        selected_model = resolve_model(data.get("model"))

        web_results = []
        if web_enabled:
            web_results, web_error = fetch_google_results(user_message)
            if web_error == "not_configured":
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Web Mode is enabled but Google lookup is not configured. Set GOOGLE_API_KEY and GOOGLE_CSE_ID.",
                        }
                    ),
                    400,
                )

        if rag_enabled and should_auto_ingest(user_message):
            filename, chunks_added = ingest_pasted_document(user_message)
            return jsonify(
                {
                    "success": True,
                    "message": (
                        f"Document saved from chat as {filename} with {chunks_added} chunks. "
                        "Now ask your question and I will use it in RAG mode."
                    ),
                    "model": selected_model,
                    "rag_enabled": True,
                    "rag_ingested": True,
                    "rag_total_chunks": rag_counts()[1],
                    "web_enabled": web_enabled,
                }
            )

        messages = build_messages(
            user_message,
            conversation_history,
            rag_enabled,
            web_enabled,
            web_results,
        )

        ollama_response = HTTP_SESSION.post(
            f"{OLLAMA_URL}/api/chat",
            json={
            "model": selected_model,
                "messages": messages,
                "stream": False,
                "keep_alive": OLLAMA_KEEP_ALIVE,
                "options": {
                    "temperature": OLLAMA_TEMPERATURE,
                    "num_predict": OLLAMA_NUM_PREDICT,
                },
            },
            timeout=(5, OLLAMA_TIMEOUT_SECONDS),
        )

        if ollama_response.status_code != 200:
            raise Exception(f"Ollama API error: {ollama_response.text}")

        body = ollama_response.json()
        assistant_message = body.get("message", {}).get("content", "")

        if not assistant_message:
            raise Exception("Ollama API returned an empty response")

        return jsonify(
            {
                "message": assistant_message.strip(),
                "success": True,
                "model": selected_model,
                "rag_enabled": rag_enabled,
                "rag_ingested": False,
                "web_enabled": web_enabled,
            }
        )

    except requests.exceptions.Timeout:
        app.logger.error("Ollama request timed out")
        return (
            jsonify(
                {
                    "error": "Request timed out. The model might be loading. Please try again.",
                    "success": False,
                }
            ),
            504,
        )
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return (
            jsonify(
                {"error": "An error occurred processing your request", "success": False}
            ),
            500,
        )


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "No message provided", "success": False}), 400

        user_message = data["message"]
        conversation_history = data.get("history", [])
        rag_enabled = bool(data.get("rag_enabled", False))
        web_enabled = bool(data.get("web_enabled", False))
        selected_model = resolve_model(data.get("model"))

        web_results = []
        if web_enabled:
            web_results, web_error = fetch_google_results(user_message)
            if web_error == "not_configured":
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Web Mode is enabled but Google lookup is not configured. Set GOOGLE_API_KEY and GOOGLE_CSE_ID.",
                        }
                    ),
                    400,
                )

        if rag_enabled and should_auto_ingest(user_message):
            filename, chunks_added = ingest_pasted_document(user_message)

            def generate_ingest_ack():
                ack = (
                    f"Document saved from chat as {filename} with {chunks_added} chunks. "
                    "Now ask your question and I will use it in RAG mode."
                )
                yield json.dumps({"type": "token", "content": ack}) + "\n"
                yield (
                    json.dumps(
                        {
                            "type": "done",
                            "model": selected_model,
                            "rag_enabled": True,
                            "rag_ingested": True,
                            "web_enabled": web_enabled,
                        }
                    )
                    + "\n"
                )

            return Response(generate_ingest_ack(), mimetype="application/x-ndjson")

        messages = build_messages(
            user_message,
            conversation_history,
            rag_enabled,
            web_enabled,
            web_results,
        )

        def generate():
            try:
                response = HTTP_SESSION.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": selected_model,
                        "messages": messages,
                        "stream": True,
                        "keep_alive": OLLAMA_KEEP_ALIVE,
                        "options": {
                            "temperature": OLLAMA_TEMPERATURE,
                            "num_predict": OLLAMA_NUM_PREDICT,
                        },
                    },
                    stream=True,
                    timeout=(5, OLLAMA_TIMEOUT_SECONDS),
                )

                if response.status_code != 200:
                    error_payload = {
                        "type": "error",
                        "error": "Ollama API error",
                        "details": response.text,
                    }
                    yield json.dumps(error_payload) + "\n"
                    return

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        parsed = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = parsed.get("message", {}).get("content", "")
                    if token:
                        yield json.dumps({"type": "token", "content": token}) + "\n"

                    if parsed.get("done"):
                        yield (
                            json.dumps(
                                {
                                    "type": "done",
                                    "model": selected_model,
                                    "rag_enabled": rag_enabled,
                                    "rag_ingested": False,
                                    "web_enabled": web_enabled,
                                }
                            )
                            + "\n"
                        )
                        return
            except requests.exceptions.Timeout:
                yield json.dumps({"type": "error", "error": "Request timed out"}) + "\n"
            except Exception as exc:
                yield (
                    json.dumps(
                        {"type": "error", "error": "Streaming failed", "details": str(exc)}
                    )
                    + "\n"
                )

        return Response(generate(), mimetype="application/x-ndjson")
    except Exception as exc:
        app.logger.error(f"Error in stream endpoint: {exc}")
        return jsonify({"error": "Failed to start stream", "success": False}), 500


@app.route("/api/health", methods=["GET"])
def health():
    ready = ollama_is_ready()
    status = "healthy" if ready else "degraded"

    return (
        jsonify(
            {
                "status": status,
                "service": "devops-chatbot",
                "ollama": "reachable" if ready else "unreachable",
                "model": OLLAMA_MODEL,
                "web_lookup": "configured" if web_lookup_configured() else "not_configured",
            }
        ),
        200 if ready else 503,
    )


init_rag_db()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    app.run(host=host, port=port, debug=debug)
