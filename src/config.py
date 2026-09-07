"""Configuração via variáveis de ambiente (ver .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Postgres do Directus (app "kobi") — via túnel SSH em dev, direto na rede
# `coolify` quando deployado na VPS (ver CLAUDE.md).
PG_HOST = os.environ.get("DIRECTUS_DB_HOST", "127.0.0.1")
PG_PORT = int(os.environ.get("DIRECTUS_DB_PORT", "5433"))
PG_DBNAME = os.environ.get("DIRECTUS_DB_NAME", "directus")
PG_USER = os.environ.get("DIRECTUS_DB_USER", "directus")
PG_PASSWORD = os.environ.get("DIRECTUS_DB_PASSWORD", "")

# Neo4j (experimento2026) — endpoint público, ver experimento2026/CLAUDE.md.
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt+s://neo4j.brunokobi.duckdns.org:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

# Modelo tabular final: scores.csv + metadata.json (gerados por
# experimento2026/scripts/treinar_modelo_final.py). Em dev, lidos direto de
# lá; em produção (container), copiados pra ./models/ e montados em
# /app/models (ver Dockerfile/docker-compose.yml) — MODELO_DIR sobrepõe
# tudo quando setado.
_EXPERIMENTO2026_DIR = Path(os.environ.get("EXPERIMENTO2026_DIR", "/home/bruno/experimento2026"))
MODELO_DIR = Path(os.environ["MODELO_DIR"]) if os.environ.get("MODELO_DIR") \
    else _EXPERIMENTO2026_DIR / "models" / "tabular_final"

# n8n — workflow que chama o Ollama pra redigir o parecer final.
N8N_WEBHOOK_PARECER = os.environ.get("N8N_WEBHOOK_PARECER", "")
