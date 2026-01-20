FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create a writable directory for cache/downloads to avoid permission errors
RUN mkdir -p /code/cache && chmod 777 /code/cache
ENV XDG_CACHE_HOME=/code/cache

COPY . .

# Expose port 7860 for Hugging Face Spaces
EXPOSE 7860

# Run the application on port 7860
CMD ["python", "app.py"]
