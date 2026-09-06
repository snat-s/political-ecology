FROM node:22.23.1-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN npm install --global @earendil-works/pi-coding-agent@0.84.4
COPY harness /opt/experiment/harness
COPY INSTRUCTIONS.md /opt/experiment/INSTRUCTIONS.md
WORKDIR /experiment
ENV PYTHONPATH=/opt/experiment
CMD ["python3", "-m", "harness.fleet"]
