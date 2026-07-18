FROM python:3.10-slim

# Chromium install for Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py .

# Set environment variables
ENV BOT_TOKEN="8953778114:AAGlkAXZfazrAArDl7vKvbBvp9EuFm91r68"
ENV CHAT_ID="-1004306819565"

CMD ["python", "bot.py"]
