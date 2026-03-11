FROM python:3.11-slim

# Install git and other required tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir boto3

# Create gitsync user (non-root)
RUN useradd -m -u 1000 -s /bin/bash gitsync && \
    mkdir -p /dag-catalog/repos /dag-catalog/current && \
    chown -R gitsync:gitsync /dag-catalog

# Copy sync script
COPY sync-repos.py /usr/local/bin/sync-repos.py
RUN chmod +x /usr/local/bin/sync-repos.py

# Switch to non-root user
USER gitsync

# Set working directory
WORKDIR /dag-catalog

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/sync-repos.py"]
