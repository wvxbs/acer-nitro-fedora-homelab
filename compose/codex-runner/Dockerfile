FROM node:22-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive     CODEX_HOME=/home/node/.codex

RUN apt-get update     && apt-get install -y --no-install-recommends         bash ca-certificates curl git openssh-client python3 ripgrep sudo     && rm -rf /var/lib/apt/lists/*     && echo "node ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/node     && npm install -g @openai/codex

USER node
WORKDIR /workspace

CMD ["bash", "-lc", "while true; do sleep 3600; done"]
