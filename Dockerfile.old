FROM ghcr.io/surnet/alpine-python-wkhtmltopdf:3.13.0-0.12.6-full

# Set the working directory in the container to /app
WORKDIR /app

# Copy your Flask app and requirements.txt into the container
COPY ./ /app

# Install Python dependencies from the requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

# Expose port 5000 to access the Flask app
EXPOSE 5000

# Set the entrypoint to run the Flask app
CMD ["python3", "app.py"]
