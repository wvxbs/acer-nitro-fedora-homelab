FROM fedora:41

RUN dnf install -y bash ttyd util-linux && \
    dnf clean all && \
    rm -rf /var/cache/dnf

COPY entrypoint.sh /usr/local/bin/host-terminal-entrypoint
COPY host-login.sh /usr/local/bin/host-login
COPY host-shell.sh /usr/local/bin/host-shell

RUN chmod 0755 /usr/local/bin/host-terminal-entrypoint /usr/local/bin/host-login /usr/local/bin/host-shell

EXPOSE 7681

ENTRYPOINT ["/usr/local/bin/host-terminal-entrypoint"]
