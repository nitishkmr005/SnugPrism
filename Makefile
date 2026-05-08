.PHONY: start stop dev-backend dev-frontend seed seed-full check build-backend test-pdf

start: ## Start Qdrant, MongoDB, backend, and frontend — open UI at http://localhost:3000
	@bash -c '\
		echo "=== SnugPrism ==="; \
		echo "→ Qdrant..."; \
		docker start qdrant 2>/dev/null || docker run -d -p 6333:6333 --name qdrant qdrant/qdrant > /dev/null; \
		echo "→ MongoDB..."; \
		docker start mongodb 2>/dev/null || docker run -d -p 27017:27017 --name mongodb mongo:7 > /dev/null; \
		echo "→ Waiting 5s for databases..."; \
		sleep 5; \
		echo "→ Backend (port 8000)..."; \
		(cd backend && uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >> /tmp/snugprism-backend.log 2>&1) & \
		sleep 4; \
		echo "→ Frontend (port 3000)..."; \
		(cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev >> /tmp/snugprism-frontend.log 2>&1) & \
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

check:  ## Health check against local backend
	curl -s http://localhost:8000/api/health | python3 -m json.tool

build-backend:  ## Build Docker image
	docker build -t snugprism-backend ./backend

test-pdf:  ## Test PDF extraction
	cd backend && PYTHONPATH=. uv run python scripts/ingest_pdf.py ../resume/NitishHarsoorResume_2026.pdf

setup:  ## Install Codex CLI (required for Q&A generation)
	@command -v codex >/dev/null 2>&1 \
		&& echo "✓ Codex already installed: $$(codex --version 2>/dev/null || echo 'ok')" \
		|| (npm install -g @openai/codex && echo "✓ Codex installed")
