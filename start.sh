#!/usr/bin/env bash
# ──────────────────────────────────────────────
#  HealthAI – Start both servers (Mac / Linux)
#  Run from the project root: chmod +x start.sh && ./start.sh
# ──────────────────────────────────────────────

echo "Starting HealthAI API (FastAPI) on port 8000..."
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!

sleep 2

echo "Starting HealthAI UI (Streamlit) on port 8501..."
streamlit run ui/app.py --server.port 8501 &
UI_PID=$!

echo ""
echo "✅  HealthAI is running!"
echo "   API:  http://127.0.0.1:8000"
echo "   UI:   http://localhost:8501"
echo "   Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait and forward signals
trap "kill $API_PID $UI_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait $API_PID $UI_PID
