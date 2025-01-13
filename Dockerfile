# Use the CentOS 8 image as the base image
FROM centos:8

# Install EPEL repository and necessary dependencies
RUN dnf install -y \
    epel-release \
    gcc \
    wget \
    curl \
    make \
    python3 \
    python3-devel \
    python3-pip \
    wkhtmltopdf \
    xorg-x11-server-Xvfb \
    cairo \
    pango \
    gdk-pixbuf2 \
    qt5-qtbase \
    qt5-qtwebkit \
    && dnf clean all

# Set the environment variable to non-interactive mode to avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

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
