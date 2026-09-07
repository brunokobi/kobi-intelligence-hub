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

# Modelo tabular final (experimento2026/models/tabular_final/), reaproveitado
# via sys.path — ver src/score_preditivo.py.
EXPERIMENTO2026_DIR = Path(os.environ.get("EXPERIMENTO2026_DIR", "/home/bruno/experimento2026"))
MODELO_DIR = EXPERIMENTO2026_DIR / "models" / "tabular_final"

# n8n — workflow que chama o Ollama pra redigir o parecer final.
N8N_WEBHOOK_PARECER = os.environ.get("N8N_WEBHOOK_PARECER", "")
