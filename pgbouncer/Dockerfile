FROM edoburu/pgbouncer

USER root
RUN apk add --no-cache dos2unix

COPY generate-userlist.sh /etc/pgbouncer/generate-userlist.sh
RUN chmod +x /etc/pgbouncer/generate-userlist.sh && \
    chown postgres:postgres /etc/pgbouncer/generate-userlist.sh

ENV POSTGRES_HOST=db \
    POSTGRES_PORT=5432 \
    POSTGRES_DB=app

USER postgres

CMD ["/bin/sh", "-c", "echo 'Generating userlist...' && \
     /etc/pgbouncer/generate-userlist.sh && \
     echo 'Starting pgbouncer...' && \
     pgbouncer /etc/pgbouncer/pgbouncer.ini"] 