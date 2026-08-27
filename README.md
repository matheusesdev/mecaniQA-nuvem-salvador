# MecaniQA Nuvem Salvador

Entrega da equipe Salvador para a OAT 1 de Docker, Docker Compose e Kubernetes.

## Escopo desta sessão

Este estado do repositório corresponde somente ao Encontro 1 (26/08/2026): empacotamento e validação isolada da API Java, do MySQL e do Redis com Docker.

Ainda não fazem parte desta sessão: Docker Compose, Kubernetes, K9s, Terraform e a apresentação final.

## Equipe registrada no guia

- Matheus Espírito Santo dos Santos - Desenvolvedor Piloto
- Albert Santos Soares - Copiloto (Revisor de Lógica) e Analista de Qualidade (QA)
- Rafael Pires Araújo - Arquiteto de Software / Documentador
- Juan Pablo Barros Carvalho - Scrum Master

## Decisão técnica da equipe

A API usa `eclipse-temurin:17-jdk-alpine`, conforme decidido no brainstorm. A imagem fornece o JDK 17 e usa Alpine Linux. O contêiner documenta a porta `8080`, e a aplicação Java é o processo principal por meio do `ENTRYPOINT ["java", "-jar", "app.jar"]`.

## Pré-requisito

- Docker Engine ou Docker Desktop em execução.

Os comandos abaixo devem ser executados na raiz do repositório.

## 1. API Java

Construir a imagem:

```bash
docker build -t mecaniqa-api:encontro1 ./api
```

Executar em primeiro plano e publicar a porta `8080`:

```bash
docker run --name mecaniqa-api -p 8080:8080 mecaniqa-api:encontro1
```

Em outro terminal, validar a resposta:

```bash
curl http://localhost:8080/health
```

Resposta esperada:

```json
{"status":"UP","service":"mecaniqa-api"}
```

## 2. MySQL

Construir a imagem:

```bash
docker build -t mecaniqa-mysql:encontro1 ./mysql
```

Executar isoladamente com persistência em volume nomeado:

```bash
docker run --name mecaniqa-mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=mecaniqa_root -e MYSQL_DATABASE=mecaniqa -v mecaniqa-mysql-data:/var/lib/mysql -d mecaniqa-mysql:encontro1
```

Validar o ciclo de vida e a saúde:

```bash
docker ps --filter name=mecaniqa-mysql
docker inspect --format '{{.State.Health.Status}}' mecaniqa-mysql
docker logs mecaniqa-mysql
```

> A senha acima é apenas para desenvolvimento local. Não deve ser reutilizada em produção.

## 3. Redis

Construir a imagem:

```bash
docker build -t mecaniqa-redis:encontro1 ./redis
```

Executar isoladamente com persistência em volume nomeado:

```bash
docker run --name mecaniqa-redis -p 6379:6379 -v mecaniqa-redis-data:/data -d mecaniqa-redis:encontro1
```

Validar a saúde e a resposta do serviço:

```bash
docker inspect --format '{{.State.Health.Status}}' mecaniqa-redis
docker exec mecaniqa-redis redis-cli ping
```

A resposta esperada do último comando é `PONG`.

## Encerrar os testes

```bash
docker stop mecaniqa-api mecaniqa-mysql mecaniqa-redis
docker rm mecaniqa-api mecaniqa-mysql mecaniqa-redis
```

Os volumes nomeados permanecem preservados para demonstrar persistência. A remoção deles não faz parte deste roteiro.
