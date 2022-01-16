DB_URI=postgresql://postgres:postgres@postgres:5432/crosschat poetry run alembic upgrade head
poetry run task start
