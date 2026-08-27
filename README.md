# MecaniQA Nuvem Salvador

Entrega da equipe Salvador para a OAT 1 de Docker, Docker Compose e Kubernetes.

## Escopo desta sessao

Este estado do repositorio corresponde somente ao Encontro 1 (26/08/2026): empacotamento e validacao isolada da API Java, do MySQL e do Redis com Docker.

Ainda nao fazem parte desta sessao: Docker Compose, Kubernetes, K9s, Terraform e a apresentacao final.

## Equipe registrada no guia

- Matheus Espirito Santo dos Santos - Desenvolvedor Piloto
- Albert Santos Soares - Copiloto (Revisor de Logica) e Analista de Qualidade (QA)
- Rafael Pires Araujo - Arquiteto de Software / Documentador
- Juan Pablo Barros Carvalho - Scrum Master

## Decisao tecnica da equipe

A API usa `eclipse-temurin:17-jdk-alpine`, conforme decidido no brainstorm. A imagem fornece o JDK 17 e usa Alpine Linux. O container documenta a porta `8080`, e a aplicacao Java e o processo principal por meio de `ENTRYPOINT ["java", "-jar", "app.jar"]`.

## Pre-requisito

- Docker Engine ou Docker Desktop em execucao.

Os comandos abaixo devem ser executados na raiz do repositorio.

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

Executar isoladamente com persistencia em volume nomeado:

```bash
docker run --name mecaniqa-mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=mecaniqa_root -e MYSQL_DATABASE=mecaniqa -v mecaniqa-mysql-data:/var/lib/mysql -d mecaniqa-mysql:encontro1
```

Validar o ciclo de vida e a saude:

```bash
docker ps --filter name=mecaniqa-mysql
docker inspect --format '{{.State.Health.Status}}' mecaniqa-mysql
docker logs mecaniqa-mysql
```

> A senha acima e apenas para desenvolvimento local. Nao deve ser reutilizada em producao.

## 3. Redis

Construir a imagem:

```bash
docker build -t mecaniqa-redis:encontro1 ./redis
```

Executar isoladamente com persistencia em volume nomeado:

```bash
docker run --name mecaniqa-redis -p 6379:6379 -v mecaniqa-redis-data:/data -d mecaniqa-redis:encontro1
```

Validar a saude e a resposta do servico:

```bash
docker inspect --format '{{.State.Health.Status}}' mecaniqa-redis
docker exec mecaniqa-redis redis-cli ping
```

A resposta esperada do ultimo comando e `PONG`.

## Encerrar os testes

```bash
docker stop mecaniqa-api mecaniqa-mysql mecaniqa-redis
docker rm mecaniqa-api mecaniqa-mysql mecaniqa-redis
```

Os volumes nomeados permanecem preservados para demonstrar persistencia. A remocao deles nao faz parte deste roteiro.
