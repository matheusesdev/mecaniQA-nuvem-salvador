# syntax=docker/dockerfile:1

FROM eclipse-temurin:17-jdk-alpine AS build

WORKDIR /build
COPY src/Main.java ./Main.java
RUN javac Main.java && jar --create --file app.jar --main-class Main Main.class

FROM eclipse-temurin:17-jdk-alpine

WORKDIR /app
COPY --from=build /build/app.jar ./app.jar

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/health >/dev/null || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
