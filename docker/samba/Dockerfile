FROM alpine:latest

RUN apk add --no-cache samba-server

COPY smb.conf /etc/samba/smb.conf

RUN adduser -D testuser && \
    echo -e "testpass\ntestpass" | smbpasswd -a testuser -s

EXPOSE 445

CMD ["smbd", "--foreground", "--no-process-group"]
