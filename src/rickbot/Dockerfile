FROM python:3.13-slim

EXPOSE 8080
WORKDIR /app

COPY . ./

# Runs in its own layer, so cached by Docker
RUN pip install uv

# Allow uv to cache previously downloaded packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
