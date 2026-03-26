set -e

docker compose up -d

streamlit run ./src/main.py