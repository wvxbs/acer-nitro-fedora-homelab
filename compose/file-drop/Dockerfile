FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    coreutils \
    findutils \
    procps \
    samba \
    smbclient \
    tini \
    wsdd \
  && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/file-drop-entrypoint
COPY cleanup.sh /usr/local/bin/drop-cleanup

RUN chmod 0755 /usr/local/bin/file-drop-entrypoint /usr/local/bin/drop-cleanup

EXPOSE 137/udp 138/udp 139/tcp 3702/udp 445/tcp 5357/tcp

ENTRYPOINT ["tini", "--", "/usr/local/bin/file-drop-entrypoint"]
