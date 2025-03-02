FROM jrottenberg/ffmpeg:4.4-ubuntu

# Install Python
RUN apt-get update && \
    apt-get install -y python3-pip python3.11 && \
    ln -s /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=10000

# Expose the port
EXPOSE ${PORT}

# Command to run the application
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT}", "--log-level", "debug"] 