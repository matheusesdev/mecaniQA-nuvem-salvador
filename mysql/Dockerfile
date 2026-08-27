# syntax=docker/dockerfile:1

FROM mysql:8.4

EXPOSE 3306

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
  CMD mysqladmin ping --host=127.0.0.1 --silent || exit 1

CMD ["mysqld"]
