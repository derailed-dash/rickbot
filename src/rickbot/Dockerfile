FROM python:3.12

EXPOSE 8080
WORKDIR /app

COPY . ./

# Install Node.js - needed for pytubefix
RUN apt-get update && apt-get install -y nodejs

RUN pip install -r requirements.txt

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
