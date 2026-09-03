# MecaniQA Nuvem Salvador

Entrega da equipe Salvador para a OAT 1 de Docker, Docker Compose e Kubernetes.

## Escopo desta sessão

Este estado do repositório contempla os encontros de 26/08/2026 e 02/09/2026:

- empacotamento isolado da API Java, do MySQL e do Redis;
- orquestração dos três serviços com Docker Compose;
- comunicação pelo DNS interno do Docker (`db` e `redis`);
- persistência estruturada por volumes nomeados.

Kubernetes, K9s, Terraform e a apresentação final ainda não fazem parte desta sessão.

## Equipe registrada no guia - 26/08

- Matheus Espírito Santo dos Santos - Desenvolvedor Piloto
- Albert Santos Soares - Copiloto (Revisor de Lógica) e Analista de Qualidade (QA)
- Rafael Pires Araújo - Arquiteto de Software / Documentador
- Juan Pablo Barros Carvalho - Scrum Master

## Equipe registrada no guia - 02/09

- Matheus Espírito Santo dos Santos - Desenvolvedor Piloto
- Rafael Pires Araújo - Copiloto
- Albert Santos Soares - Arquiteto de Software / Documentador
- Juan Pablo Barros Carvalho - Scrum Master
- QA - não preenchido no guia

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

## 4. Entrega do Encontro 2 - Docker Compose

Construir e iniciar todo o ecossistema com um único comando:

```bash
docker compose up --build -d
```

O Compose cria uma rede interna compartilhada. Nela, a API resolve o MySQL pelo nome
`db` e o Redis pelo nome `redis`, sem IPs fixos. A API só é iniciada depois que os
health checks dos dois serviços indicam que eles estão prontos.

Verificar os três contêineres:

```bash
docker compose ps
```

Testar a API e a comunicação entre as camadas:

```bash
curl http://localhost:8080/health
```

Resposta esperada:

```json
{"status":"UP","service":"mecaniqa-api","mysql":"UP","redis":"UP"}
```

O endpoint retorna HTTP 503 e identifica a dependência como `DOWN` se a API não
conseguir abrir uma conexão com o MySQL ou o Redis pelos nomes internos.

Os dados ficam fora do ciclo de vida dos contêineres nos volumes `mysql_data` e
`redis_data`. Para reiniciar os serviços preservando os volumes:

```bash
docker compose down
docker compose up -d
```

Para acompanhar a inicialização e diagnosticar erros:

```bash
docker compose logs -f
```

## Requisitos do encontro de 02/09 e evidências

| Requisito | Implementação | Resultado |
| --- | --- | --- |
| Subir API, MySQL e Redis juntos | Os serviços `api`, `db` e `redis` estão no `docker-compose.yml` | Ambiente iniciado com `docker compose up --build -d` |
| Usar DNS interno, sem IP fixo | A API recebe `DB_HOST=db` e `REDIS_HOST=redis` | Nomes resolvidos na rede compartilhada |
| Aguardar as dependências | MySQL e Redis possuem health checks e a API usa `depends_on: condition: service_healthy` | API inicia depois das dependências saudáveis |
| Testar a comunicação entre as camadas | `/health` abre conexões com MySQL e Redis usando host e porta configurados | HTTP 200 com MySQL e Redis em estado `UP` |
| Preservar os dados | Volumes nomeados em `/var/lib/mysql` e `/data` | Dados permanecem fora do ciclo de vida dos contêineres |

### Teste integrado executado

Com os três contêineres ativos, foi executado:

```powershell
curl.exe http://localhost:8080/health
```

Resultado obtido:

```json
{"status":"UP","service":"mecaniqa-api","mysql":"UP","redis":"UP"}
```

Esse resultado confirma simultaneamente que a API responde na porta publicada
`8080`, que os nomes `db` e `redis` são resolvidos pelo DNS interno e que as portas
dos dois serviços podem ser alcançadas pela API.

### Observações de escopo

- A verificação atual comprova conectividade TCP entre as camadas; operações de
  negócio, consultas SQL e comandos Redis serão responsabilidade da evolução da API.
- As credenciais declaradas são exclusivas para o ambiente didático local e não
  devem ser usadas em produção.
- A remoção completa dos volumes com `docker compose down -v` apaga os dados e,
  por isso, não faz parte do procedimento normal de encerramento.
