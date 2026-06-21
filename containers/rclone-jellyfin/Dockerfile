FROM alpine:3.22

RUN apk add --no-cache \
    ca-certificates \
    fuse3 \
    rclone \
    tini

COPY entrypoint.sh /usr/local/bin/rclone-jellyfin-entrypoint
RUN chmod +x /usr/local/bin/rclone-jellyfin-entrypoint

ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/rclone-jellyfin-entrypoint"]
