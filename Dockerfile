# 1. Use an official lightweight Python runtime
FROM python:3.12-slim

# 2. Set the working directory inside the cloud container
WORKDIR /workspace

# 3. Copy and install dependencies first (optimizes build caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your application files
COPY . .

# 5. Expose the standard Hugging Face traffic port
EXPOSE 7860

# 6. Launch Streamlit with strict routing rules for Hugging Face
CMD ["streamlit", "run", "app.py", "--server.port=7860",
"--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]