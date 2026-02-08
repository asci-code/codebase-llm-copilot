# codebase-llm-copilot

An AI agent that ingests GitHub repositories and answers architectural questions using hybrid retrieval (vector + graph) and structured reasoning. The system returns citations with file paths and line ranges to support verification.

## Architecture Overview

```
             +------------------------+
             |      FastAPI API       |
             | /ingest  /ask /trace   |
             +-----------+------------+
                         |
                         v
        +----------------+----------------+
        | Ingestion Pipeline              |
        | - clone repo                    |
        | - parse + chunk                 |
        | - extract symbols/imports       |
        +----------------+----------------+
                         |
                         v
+----------------+   +---+-----------------+   +--------------------+
| Vector Store   |   | Dependency Graph    |   | Observability       |
| (Chroma)       |   | (networkx)          |   | traces + logs       |
+--------+-------+   +---------+-----------+   +----------+---------+
         |                     |                          |
         +----------+----------+                          |
                    v                                     v
              +-----+--------------------+      +---------+-------+
              | Hybrid Retriever         |      | Trace Store     |
              | semantic + graph expand  |      +-----------------+
              +--------------+-----------+
                             v
                      +------+--------+
                      | Agent         |
                      | plan/retrieve |
                      | analyze/answer|
                      +---------------+
```

## Key Capabilities

- **Repo ingestion**: clones GitHub repositories, parses supported files, chunks by symbols when possible, and extracts metadata.
- **Embeddings + storage**: pluggable embedding provider (OpenAI or local sentence-transformers) with Chroma vector storage.
- **Dependency graph**: builds import/call graph via networkx and enables traversal expansion.
- **Hybrid retrieval**: combines semantic search with graph neighborhood expansion.
- **Agent reasoning**: plan → retrieve → analyze → answer flow with citations and confidence score.
- **Observability**: trace storage with retrieval results and timings.
- **Evaluation**: scripted evaluation of citation correctness and keyword coverage.

## Project Structure

```
app/
  config.py
  main.py
  schemas.py
agent/
  agent.py
  llm.py
  observability.py
ingestion/
  ingest.py
  parser.py
  repo.py
  types.py
retrieval/
  embeddings.py
  retriever.py
  vector_store.py
graph/
  builder.py
eval/
  run_eval.py
  questions.json
 tests/
 docker/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file based on `.env.example` to configure providers.

## Run the API

```bash
python -m app.main
```

## Example Requests

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/psf/requests"}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"repo_id":"requests-abcdef1234","question":"How is HTTP session management organized?"}'
```

## Evaluation

Run the evaluation script against a running API server:

```bash
python eval/run_eval.py https://github.com/psf/requests
```

## Docker

```bash
docker-compose up --build
```

## Notes

- **LLM providers**: set `LLM_PROVIDER=openai` and `OPENAI_API_KEY` to enable OpenAI answers.
- **Embeddings**: set `EMBEDDING_PROVIDER=openai` to use OpenAI embeddings, otherwise local sentence-transformers are used.
