FROM python:3.14-slim

# Instala dependências de sistema essenciais para o Geopandas
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala as bibliotecas (forçando a atualização do pip)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código e ficheiros .geojson e .xlsx para dentro do container
COPY . .

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "heatmap_porto.py", "--server.port=8501", "--server.address=0.0.0.0"]