FROM lhotakj/strawall_base:latest
# Base it on the Dockerfile.basedocker publisher at https://hub.docker.com/repository/docker/lhotakj/strawall_base/tags

# Set the working directory in the container to /app
WORKDIR /app

# Copy the Flask app and requirements.txt into the container
COPY ./ /app

# Install Python dependencies from the requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install -r ./requirements.txt

# Expose port 5000 to access the Flask app
EXPOSE 5000

# Set the entrypoint to run the Flask app
CMD ["python3", "app.py"]
