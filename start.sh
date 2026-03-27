set -e

docker compose up -d

uvicorn src.app:app --host 0.0.0.0 --port 8000 &

streamlit run ./src/main.py