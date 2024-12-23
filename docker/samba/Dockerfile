FROM alpine:latest

# sambaとsamba-commonパッケージをインストール
RUN apk add --no-cache samba-server samba-common-tools

COPY smb.conf /etc/samba/smb.conf

# ユーザー作成とパスワード設定
RUN adduser -D testuser && \
    (echo "testpass"; echo "testpass") | smbpasswd -a testuser

# 共有フォルダの作成と権限設定
RUN mkdir -p /share && \
    chown -R testuser:testuser /share && \
    chmod -R 755 /share

EXPOSE 445

CMD ["smbd", "--foreground", "--no-process-group"]
