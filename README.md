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

Até a entrega de 21/10/2026, esta branch possui:

- API Java conteinerizada, com endpoint `/health`;
- MySQL e Redis em contêineres próprios;
- Docker Compose com rede interna e volumes persistentes;
- Deployments, Services, PVCs, probes e limites de recursos no Kubernetes;
- simulador Python de sensores IoT instrumentado com `prometheus-client`;
- Prometheus coletando métricas do simulador;
- Grafana com exatamente quatro dashboards: CPU, Memória, Erro e Sucesso;
- quatro alarmes ativos no Grafana, HPA e coleta individual das réplicas;
- teste de estresse com evidências de disparo, escala e recuperação;
- quatro runbooks e acordo operacional com metas de continuidade;
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

## 21/10/2026 — Encontro 3: HPA, quatro alarmes e teste de estresse

### Papéis registrados

- Piloto: Juan Pablo Barros Carvalho
- Co-Piloto: Matheus Espírito Santo dos Santos
- QA: Rafael Pires Araújo
- Arquiteto / Documentador: não preenchido no caderno
- Scrum Master: Albert Santos Soares

### Decisões, código e entrega

A equipe definiu o HPA com uma a cinco réplicas do simulador, CPU em 70% e memória em 80% dos requests, com estabilização de 300 segundos para reduzir as réplicas. Os quatro alarmes do Grafana avaliam condições sustentadas por dois minutos: CPU acima de 80% do limite de 250m, memória acima de 102,4 MiB, erros acima de 5% com pelo menos vinte tentativas e sucesso abaixo de 80% da taxa esperada enquanto houver carga.

Foram entregues:

- manifesto `autoscaling/v2` em `k8s/simulator-hpa.yaml`;
- quatro regras ativas em `grafana/provisioning/alerting/alerts.yaml`, avaliadas a cada 20 segundos;
- Service headless e descoberta DNS para o Prometheus coletar cada réplica individualmente;
- preparação do Metrics Server para o Kind local;
- injeção sintética limitada de CPU, memória e erros, desativada por padrão;
- script de teste com restauração automática da configuração original;
- oito testes automatizados do simulador;
- logs, eventos, estados das regras e capturas em `docs/evidencias/2026-10-21-estresse/`.

Na execução de 23/10/2026, o HPA aumentou de uma para cinco réplicas, os quatro alarmes dispararam e, após a retirada da carga, as regras voltaram ao normal e o HPA reduziu para uma réplica. A data da sessão é 21/10; os arquivos preservam a data real da validação. O teste utiliza um gerador sintético por réplica e não mede a capacidade de ingestão de sensores reais.

Commit principal: `d7ae88e` (`feat: entrega de 21/10 com HPA alarmes e evidencias de estresse`). Branch: `entrega-oat2-21-10-hpa-alarmes`. Veja [implementação e reprodução](docs/entrega-2026-10-21-hpa-alarmes.md) e [validação da sessão](docs/validacao-2026-10-21.md).

## 21/10/2026 — Encontro 4: runbooks e continuidade dos negócios

### Papéis registrados

- Piloto: Juan Pablo Barros Carvalho
- Co-Piloto: Matheus Espírito Santo dos Santos
- QA: Rafael Pires Araújo
- Arquiteto / Documentador: não preenchido no caderno
- Scrum Master: Albert Santos Soares

### Decisões, código e entrega

A equipe definiu um runbook para cada alarme, com condição de disparo, impacto, responsável, comandos de diagnóstico, ações de recuperação, critérios de encerramento e evidências. O acordo operacional adota SLA de 99,9%, SLO de 99,95%, SLI baseado em verificações externas bem-sucedidas, RTO de 30 minutos e RPO de 15 minutos.

Foram entregues:

- quatro runbooks: [CPU](docs/runbooks/cpu.md), [Memória](docs/runbooks/memoria.md), [Erro](docs/runbooks/erro.md) e [Sucesso](docs/runbooks/sucesso.md);
- [acordo operacional](docs/acordo-operacional.md), com definições, fórmulas, período de apuração e orçamento de indisponibilidade;
- responsabilidades e passos para diagnóstico, recuperação e encerramento de incidentes;
- análise da queda de 45 minutos: ultrapassa o RTO e consome aproximadamente 8,56% do orçamento anual do SLA, sem determinar a perda de dados;
- [mapa da entrega](docs/entrega-2026-10-21-continuidade.md), relacionando as decisões aos documentos e às evidências da sessão anterior.

SLA, SLO, RTO e RPO são metas acadêmicas formalizadas. O teste local não demonstra disponibilidade anual, recuperação de uma região inteira ou cumprimento do RPO por restauração de banco de dados.

Commit principal: `4b5cbde` (`docs: entrega de 21/10 com runbooks e acordo de continuidade`). Branch: `entrega-oat2-21-10-runbooks-continuidade`. Esta branch inclui a implementação e as evidências da primeira entrega.

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

Abra `http://localhost:9090` para consultar as métricas e `http://localhost:3000` para visualizar a pasta **MecaniQA OAT 2**.

O acesso padrão do Grafana local é usuário **`admin`** e senha **`MecaniQA@2026!`**.
Essa credencial é pública e exclusiva do laboratório local. Novas instalações
recebem esse padrão; instalações existentes mantêm sua senha até executar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare-grafana.ps1 -ResetLocalCredentials
```

O comando atualiza o Secret e a senha já persistida no Grafana, preservando os
dashboards e as regras. Credenciais de outros ambientes devem ser próprias.

## Evidências e limites

- Docker, Compose, Kubernetes e K9s: [docs/validacao-2026-10-06.md](docs/validacao-2026-10-06.md).
- Simulador e Prometheus: [docs/validacao-2026-10-07.md](docs/validacao-2026-10-07.md).
- Grafana e dashboards: [docs/validacao-2026-10-14.md](docs/validacao-2026-10-14.md).
- HPA, alarmes e estresse: [docs/validacao-2026-10-21.md](docs/validacao-2026-10-21.md), com execução registrada em 23/10/2026.
- CPU e memória representam o processo Python, não todo o nó.
- Em 21/10, a coleta passa a descobrir cada réplica via DNS headless; a validação atual está no relatório dessa sessão.
- As capturas de 14/10 representam carga sintética normal, não teste de estresse.
- As metas de continuidade estão documentadas; desastre regional e restauração de dados não foram testados.
- Credenciais versionadas são exclusivamente didáticas.

O README distingue configuração, implementação e validação histórica; a presença de um arquivo não substitui evidência de execução.
