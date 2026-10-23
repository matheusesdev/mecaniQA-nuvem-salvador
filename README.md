# MecaniQA Nuvem Salvador

Projeto acadêmico de Cloud/DevOps desenvolvido pela equipe Salvador durante as OATs 1 e 2. O repositório registra, em ordem cronológica, a evolução de uma aplicação inicialmente conteinerizada até uma arquitetura Kubernetes monitorada por Prometheus e Grafana.

## Contexto do trabalho

No cenário apresentado pelo professor, a **MecâniQA - Automotive Tech** é uma startup de Feira de Santana voltada à gestão de lojas de autopeças, auto centers e oficinas mecânicas. Durante um programa de trainee, as equipes assumem o papel de profissionais responsáveis por evoluir a infraestrutura da plataforma.

O trabalho segue uma dinâmica inspirada em SCRUM. Cada sessão síncrona dura aproximadamente 90 minutos e possui um guia, papéis definidos, discussão em equipe e uma entrega prática. O fluxo esperado inclui:

1. entendimento do problema e distribuição dos papéis;
2. brainstorm de fatos, questões e ideias;
3. modelagem da solução e criação dos cenários de teste;
4. implementação em dupla;
5. testes e validação pelo QA;
6. consolidação do código, das evidências e da apresentação.

Os papéis previstos são Desenvolvedor Piloto, Co-Piloto, Analista de Qualidade (QA), Arquiteto de Software / Documentador e Scrum Master / Apresentador. Campos não preenchidos nos cadernos são mantidos como não registrados.

> A MecâniQA é o cenário acadêmico fornecido para a atividade. Este repositório não representa uma plataforma comercial completa nem comprova dados reais da empresa descrita no enunciado.

## Membros do time Salvador

- Matheus Espírito Santo dos Santos
- Albert Santos Soares
- Rafael Pires Araújo
- Juan Pablo Barros Carvalho

O documento de estrutura prevê times de cinco pessoas. Este repositório registra
os quatro integrantes identificados nos cadernos da equipe; eventuais exceções de
composição devem ser confirmadas com o professor.

## Estado atual

A base de 14/10/2026 possui os componentes abaixo; a seção de 21/10 registra a evolução nesta branch:

- API Java conteinerizada, com endpoint `/health`;
- MySQL e Redis em contêineres próprios;
- Docker Compose com rede interna e volumes persistentes;
- Deployments, Services, PVCs, probes e limites de recursos no Kubernetes;
- simulador Python de sensores IoT instrumentado com `prometheus-client`;
- Prometheus coletando métricas do simulador;
- Grafana com exatamente quatro dashboards: CPU, Memória, Erro e Sucesso;
- scripts e registros de validação para reproduzir e auditar as entregas.

A API Java demonstra conectividade TCP com MySQL e Redis. Ela não implementa as funções completas de gestão de oficinas, não executa consultas de negócio e não recebe os dados gerados pelo simulador IoT. O simulador e a stack de monitoração formam uma demonstração separada de observabilidade.

## Arquitetura atual

```text
Simulador IoT :8000 --> Prometheus :9090 --> Grafana :3000

API Java :8080 -----> MySQL :3306
        |
        +------------> Redis :6379
```

No cluster, os recursos ficam no namespace `mecaniqa`. MySQL e Redis são internos (`ClusterIP`), enquanto a API usa `NodePort` 30080. No Kind local, essa porta é encaminhada para `http://localhost:18080`.

# OAT 1 — Conteinerização e orquestração

## 26/08/2026 — Encontro 1: Docker

### Papéis registrados

- Piloto: Matheus Espírito Santo dos Santos
- Co-Piloto: não preenchido no caderno
- QA: Albert Santos Soares
- Arquiteto / Documentador: Rafael Pires Araújo
- Scrum Master: Juan Pablo Barros Carvalho

### Decisões, código e entrega

A equipe escolheu `eclipse-temurin:17-jdk-alpine` para a aplicação Java, `EXPOSE 8080` para documentar a porta e `ENTRYPOINT ["java", "-jar", "app.jar"]` para manter a aplicação como processo principal.

Foram entregues:

- Dockerfile multi-stage para a API Java em `api/Dockerfile`;
- Dockerfiles próprios para MySQL 8.4 e Redis 7.4;
- portas, comandos de inicialização e health checks;
- instruções de build, execução e inspeção dos três serviços.

Commit principal: `9c06378` (`feat: entrega do encontro 1 com Docker`). Ele foi registrado em 27/08/2026; o histórico não comprova publicação no mesmo dia do encontro.

```powershell
docker build -t mecaniqa-api:encontro1 ./api
docker run --name mecaniqa-api -p 8080:8080 mecaniqa-api:encontro1
curl.exe -i http://localhost:8080/health
```

Sem os bancos, a API responde HTTP 503 e identifica MySQL e Redis como `DOWN`. Isso demonstra que o servidor está ativo, mas suas dependências não estão.

## 02/09/2026 — Encontro 2: Docker Compose

### Papéis registrados

- Piloto: Matheus Espírito Santo dos Santos
- Co-Piloto: Rafael Pires Araújo
- QA: não preenchido no caderno
- Arquiteto / Documentador: Albert Santos Soares
- Scrum Master: Juan Pablo Barros Carvalho

### Decisões, código e entrega

A API passaria a localizar os bancos pelo DNS interno do Docker, usando `db` para MySQL e `redis` para Redis, sem IPs fixos. Os dados seriam armazenados fora do ciclo de vida dos contêineres.

Foram entregues:

- `docker-compose.yml` com `api`, `db` e `redis`;
- rede interna, `DB_HOST=db` e `REDIS_HOST=redis`;
- health checks e espera por dependências saudáveis;
- volumes `mysql_data` e `redis_data`;
- inicialização do ambiente com um único comando.

Commit principal: `57513d8` (`feat: implementa entrega Docker Compose do encontro 2`).

```powershell
docker compose up --build -d
docker compose ps
curl.exe http://localhost:8080/health
```

Resposta integrada esperada:

```json
{"status":"UP","service":"mecaniqa-api","mysql":"UP","redis":"UP"}
```

Use `docker compose down` para encerrar preservando os volumes. `docker compose down -v` remove os dados e não faz parte do fluxo normal.

## 09/09/2026 — Encontro 3: Kubernetes e K9s

### Papéis registrados

- Piloto: Juan Pablo
- Co-Piloto: Matheus Santos
- QA, Arquiteto e Scrum Master: não preenchidos no caderno

### Decisões, código e entrega

Deployments manteriam o estado desejado e recriariam Pods em caso de falha. MySQL e Redis seriam acessíveis somente dentro do cluster por `ClusterIP`, e a API seria exposta por `NodePort` ou `LoadBalancer`.

Foram entregues:

- namespace `mecaniqa`;
- Deployments e Services para API, MySQL e Redis;
- API em `NodePort` 30080;
- MySQL e Redis em `ClusterIP`;
- PVCs, probes, requests e limits;
- cluster Kind local e inspeção por kubectl e K9s.

Commit principal: `8ef39e6` (`feat: implementa entrega Kubernetes`), registrado em 10/09/2026. A execução, a recuperação de Pod e a persistência estão em [docs/validacao-kubernetes.md](docs/validacao-kubernetes.md).

# OAT 2 — Monitorando a continuidade

## 07/10/2026 — Encontro 1: métricas IoT e Prometheus

### Papéis registrados

- Piloto: Rafael Pires Araújo
- Co-Piloto: não preenchido no caderno
- QA: Albert Santos Soares
- Arquiteto / Documentador: Juan Pablo Barros Carvalho
- Scrum Master: Matheus Espírito Santo dos Santos

### Decisões, código e entrega

Observabilidade foi definida como acompanhar o comportamento da aplicação, não apenas verificar se o servidor está ligado. A equipe decidiu instrumentar o simulador Python com `prometheus-client`, expor `/metrics` e permitir que o Prometheus coletasse e armazenasse as séries temporais.

Foram entregues:

- simulador Python em `simulator/`;
- métricas de leituras, falhas dos sensores, erros, duração, operações em andamento e janelas de pico;
- endpoint `/metrics` na porta 8000;
- Deployment e Service do simulador;
- ConfigMap, PVC, Deployment e Service do Prometheus;
- scrape do job `iot-simulator` a cada 15 segundos;
- seis testes automatizados.

Commit principal: `dcd9343` (`feat: adiciona métricas IoT e coleta Prometheus`). Veja [docs/projeto-metricas.md](docs/projeto-metricas.md) e [docs/validacao-2026-10-07.md](docs/validacao-2026-10-07.md).

## 14/10/2026 — Encontro 2: Grafana e quatro dashboards

### Papéis registrados

- Piloto: Matheus Espírito Santo dos Santos
- Co-Piloto: Rafael Pires Araújo
- QA: não preenchido no caderno
- Arquiteto / Documentador: Albert Santos Soares (AUSENTE)
- Scrum Master: Juan Pablo Barros Carvalho

### Decisões, código e entrega

A equipe decidiu provisionar exatamente quatro dashboards independentes, cada um com um painel: CPU, Memória, Erro e Sucesso. O Prometheus é a fonte de dados, e `rate()` transforma contadores acumulados em atividade recente.

Foram entregues:

- PVC, Deployment e Service do Grafana;
- datasource Prometheus provisionado;
- quatro dashboards em `grafana/dashboards/`;
- ConfigMaps reproduzíveis;
- exportação dos dashboards implantados;
- capturas e respostas das APIs em `docs/evidencias/2026-10-14/`;
- script de validação das consultas, datasource e dashboards.

| Dashboard | Consulta principal | Interpretação |
| --- | --- | --- |
| CPU | `rate(process_cpu_seconds_total[...])` | Percentual aproximado de um núcleo do processo Python |
| Memória | `process_resident_memory_bytes` | Memória residente do processo Python |
| Erro | `rate(iot_processing_errors_total[...])` | Leituras rejeitadas por segundo |
| Sucesso | `rate(iot_readings_total[...])` | Leituras processadas por segundo |

Commit principal: `62faab1` (`feat: entrega OAT2 de 14/10 com Grafana e quatro dashboards`). Veja [docs/entrega-2026-10-14.md](docs/entrega-2026-10-14.md) e [docs/validacao-2026-10-14.md](docs/validacao-2026-10-14.md).

## 21/10/2026 — Primeira entrega HPA alarmes e estresse

Branch: `entrega-oat2-21-10-hpa-alarmes`.

- HPA de uma a cinco réplicas, CPU em 70% e memória em 80% dos requests;
- quatro alarmes provisionados no Grafana, com condições sustentadas por dois minutos;
- descoberta DNS individual das réplicas pelo Prometheus;
- injeção sintética limitada e desativada por padrão;
- script de estresse com restauração automática e coleta de logs, estados e capturas.

Veja [implementação e reprodução](docs/entrega-2026-10-21-hpa-alarmes.md) e
[validação da sessão](docs/validacao-2026-10-21.md). Os testes e as evidências
registram a data real de execução, embora atendam à sessão acadêmica de 21/10.

## 21/10/2026 — Segunda entrega continuidade

Esta branch `entrega-oat2-21-10-runbooks-continuidade` inclui a primeira entrega e
a documentação complementar: [quatro runbooks e mapa da entrega](docs/entrega-2026-10-21-continuidade.md)
e [acordo operacional](docs/acordo-operacional.md), com SLA 99,9%, SLO 99,95%,
SLI externo, RTO de 30 minutos e RPO de 15 minutos.
As duas branches são locais para revisão; integração na main e publicação não
fazem parte desta preparação.

## Como executar o ambiente atual

Pré-requisitos: Docker Desktop em modo Linux, kubectl, Kind e K9s.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy-local.ps1
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
kubectl --context kind-mecaniqa -n mecaniqa get deploy,pods,svc,pvc
curl.exe --fail http://localhost:18080/health
```

Prometheus e Grafana:

```powershell
kubectl --context kind-mecaniqa -n mecaniqa port-forward service/prometheus 9090:9090
kubectl --context kind-mecaniqa -n mecaniqa port-forward service/grafana 3000:3000
```

Abra `http://localhost:9090` para consultar as métricas e `http://localhost:3000` para visualizar a pasta **MecaniQA OAT 2**. A senha do Grafana fica no Secret local e não deve ser exibida em gravações ou commits.

## Evidências e limites

- Docker, Compose, Kubernetes e K9s: [docs/validacao-2026-10-06.md](docs/validacao-2026-10-06.md).
- Simulador e Prometheus: [docs/validacao-2026-10-07.md](docs/validacao-2026-10-07.md).
- Grafana e dashboards: [docs/validacao-2026-10-14.md](docs/validacao-2026-10-14.md).
- CPU e memória representam o processo Python, não todo o nó.
- Em 21/10, a coleta passa a descobrir cada réplica via DNS headless; a validação atual está no relatório dessa sessão.
- As capturas de 14/10 representam carga sintética normal, não teste de estresse.
- Credenciais versionadas são exclusivamente didáticas.

O README distingue configuração, implementação e validação histórica; a presença de um arquivo não substitui evidência de execução.
