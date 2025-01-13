FROM python:3.12-slim

# Install your system packages using dpkg or apt
RUN apt-get update && apt-get install -y dpkg

# If you need to install a specific .deb file
COPY install/wkhtmltox_0.12.6.1-2.jammy_amd64.deb /tmp/
RUN dpkg -i /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb && rm /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Copy your application code
COPY . /app/

WORKDIR /app
CMD ["python", "app.py"]
