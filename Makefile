.PHONY: setup start stop dev-backend dev-frontend seed seed-full reindex regenerate-qas check build-backend test-pdf

setup:  ## Install backend/frontend dependencies needed to run locally
	@command -v docker >/dev/null 2>&1 || (echo "Docker is required. Install Docker Desktop first." && exit 1)
	@command -v uv >/dev/null 2>&1 || (echo "uv is required. Install it from https://docs.astral.sh/uv/ first." && exit 1)
	@command -v npm >/dev/null 2>&1 || (echo "npm is required. Install Node.js first." && exit 1)
	cd backend && uv sync
	cd frontend && npm install
	@command -v codex >/dev/null 2>&1 \
		&& echo "✓ Codex already installed: $$(codex --version 2>/dev/null || echo 'ok')" \
		|| npm install -g @openai/codex

start: setup ## Install deps, start Qdrant, MongoDB, backend, and frontend — open UI at http://localhost:3000
	@bash -c '\
		echo "=== SnugPrism ==="; \
		echo "→ Clearing old app processes..."; \
		pkill -f "uvicorn app.main" 2>/dev/null || true; \
		pkill -f "next-router-worker|next dev" 2>/dev/null || true; \
		for port in 8000 3000; do \
			pids=$$(lsof -ti tcp:$$port 2>/dev/null || true); \
			if [ -n "$$pids" ]; then kill $$pids 2>/dev/null || true; fi; \
		done; \
		echo "→ Qdrant..."; \
		docker start qdrant 2>/dev/null || docker run -d -p 6333:6333 --name qdrant qdrant/qdrant > /dev/null; \
		echo "→ MongoDB..."; \
		docker start mongodb 2>/dev/null || docker run -d -p 27017:27017 --name mongodb mongo:7 > /dev/null; \
		echo "→ Waiting 5s for databases..."; \
		sleep 5; \
		echo "→ Backend (port 8000)..."; \
		nohup bash -c "cd backend && uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" >> /tmp/snugprism-backend.log 2>&1 & \
		for i in $$(seq 1 30); do \
			curl -fsS http://localhost:8000/api/health >/dev/null 2>&1 && break; \
			sleep 1; \
		done; \
		curl -fsS http://localhost:8000/api/health >/dev/null || (echo "Backend failed. See /tmp/snugprism-backend.log" && exit 1); \
		echo "→ Frontend (port 3000)..."; \
		nohup bash -c "cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev" >> /tmp/snugprism-frontend.log 2>&1 & \
		sleep 2; \
		echo ""; \
		echo "=== All running ==="; \
		echo "  UI  → http://localhost:3000"; \
		echo "  API → http://localhost:8000/api/health"; \
		open http://localhost:3000 2>/dev/null || true; \
	'

stop: ## Stop backend, frontend, and Docker services
	@pkill -f "uvicorn app.main" 2>/dev/null || true
	@pkill -f "next-router-worker\|next dev" 2>/dev/null || true
	@for port in 8000 3000; do \
		pids=$$(lsof -ti tcp:$$port 2>/dev/null || true); \
		if [ -n "$$pids" ]; then kill $$pids 2>/dev/null || true; fi; \
	done
	@docker stop qdrant mongodb 2>/dev/null || true
	@echo "All services stopped."

dev-backend:  ## Start FastAPI backend only (port 8000, with reload)
	cd backend && uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:  ## Start Next.js frontend only (port 3000)
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

seed:  ## Seed topics + bootstrap Q&As (no LLM calls)
	cd backend && PYTHONPATH=. uv run python scripts/seed_db.py --skip-pdf --skip-hub

seed-full:  ## Full seed: topics + resume Q&As + hub content (requires OPENAI_API_KEY)
	cd backend && PYTHONPATH=. uv run python scripts/seed_db.py

seed-embeddings:  ## Seed embedding models Q&As + Learning Hub sections (no LLM calls, fast)
	cd backend && PYTHONPATH=. uv run python scripts/seed_embedding_content.py

reindex:  ## Rebuild Qdrant vectors from documents already stored in MongoDB
	cd backend && PYTHONPATH=. uv run python scripts/reindex_documents.py

regenerate-qas:  ## Regenerate MongoDB Q&As from all ingested PDFs/URLs
	cd backend && PYTHONPATH=. uv run python scripts/regenerate_qas.py

check:  ## Health check against local backend
	curl -s http://localhost:8000/api/health | python3 -m json.tool

build-backend:  ## Build Docker image
	docker build -t snugprism-backend ./backend

test-pdf:  ## Test PDF extraction
	cd backend && PYTHONPATH=. uv run python scripts/ingest_pdf.py ../resume/NitishHarsoorResume_2026.pdf
