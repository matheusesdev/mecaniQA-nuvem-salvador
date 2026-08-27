# syntax=docker/dockerfile:1

FROM redis:7.4-alpine

EXPOSE 6379

VOLUME ["/data"]

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD redis-cli ping | grep PONG || exit 1

CMD ["redis-server", "--appendonly", "yes"]
