# MecaniQA Nuvem Salvador

Entrega da equipe Salvador para a OAT 1 de Docker, Docker Compose e Kubernetes.

Última revisão documental: **06/10/2026**. Branch desta revisão:
`validacao-entregas-oat1-2026-10-06`.

## Contexto do trabalho

Este projeto acadêmico integra a OAT 1 do programa de trainee da MecâniQA Tech,
startup apresentada no enunciado como fornecedora de um sistema SaaS de gestão
e diagnóstico automotivo para oficinas mecânicas. O cenário proposto utiliza
uma aplicação Java, MySQL para dados transacionais e Redis para armazenamento
de alta velocidade, em uma infraestrutura local instável com esgotamento de recursos.

A equipe Salvador atua no papel de Engenheiros Cloud/DevOps para construir
uma fundação conteinerizada e resiliente: empacotar os serviços separadamente,
orquestrar o ambiente local, configurar comunicação e persistência e declarar
os recursos Kubernetes. A especificação geral também solicita configuração
inicial de provisionamento com Terraform, ainda ausente neste repositório.

A implementação Java deste repositório é uma API de verificação de conectividade
para demonstrar a infraestrutura. As funcionalidades de gestão e diagnóstico
descritas no cenário do produto não estão implementadas nesta API.

## Membros do time Salvador

- Matheus Espírito Santo dos Santos
- Albert Santos Soares
- Rafael Pires Araújo
- Juan Pablo Barros Carvalho

As funções registradas por encontro estão preservadas nas seções de equipe
abaixo. O documento geral prevê cinco integrantes por time e exige que exceções
sejam registradas e autorizadas pelo orientador. Este README registra os quatro
nomes existentes no projeto.

## Organização das sessões

Conforme a estrutura de sessões fornecida pelo professor, o trabalho segue
SCRUM, com distribuição de papéis, brainstorm de Fatos, Questões e Ideias,
modelagem e cenários de teste, execução em dupla, validação pelo QA e fechamento
da documentação. Os papéis são Desenvolvedor Piloto, Co-Piloto, Analista de
Qualidade, Arquiteto de Software / Documentador e Scrum Master / Apresentador.
Boards, relatórios, cenários de teste e repositório são os registros de avaliação
previstos; esta descrição da dinâmica não comprova a realização de cada atividade.

## Requisitos gerais da OAT 1 e situação do repositório

| Requisito da especificação geral | Situação na revisão de 06/10/2026 |
| --- | --- |
| Repositório `mecaniQA-nuvem-<nome_do_time>` | Nome conforme o padrão: `mecaniQA-nuvem-salvador`. |
| README com contexto e nomes dos membros | Contexto e quatro integrantes registrados neste documento, com funções por encontro preservadas. |
| Dockerfiles de Java, MySQL e Redis | Presentes em `api/`, `mysql/` e `redis/`. |
| Compose com os serviços, rede e persistência | Presente em `docker-compose.yml`; configuração validada nesta revisão. |
| Manifestos Kubernetes e configuração inicial Terraform | Manifestos em `k8s/`; não há arquivos Terraform versionados. `infra/kind.yaml` configura o cluster Kind local, não substitui Terraform. |
| Monitoramento com K9s | Pods e eventos inspecionados em 06/10/2026; CPU e memória coletadas com Metrics Server e exibidas no K9s. |
| Apresentação `mecaniQA_oat1_<nome_da_equipe>.pdf` | Existe `docs/mecaniQA-nuvem-OAT1-Salvador.pdf`, cujo nome diverge do padrão solicitado `mecaniQA_oat1_salvador.pdf`. |
| Link na tabela de Equipes e convite ao professor `lasilva` | Procedimentos de entrega previstos na especificação geral. |
| Apresentação no modelo e submissão no Blackboard | PDF presente; conformidade com o modelo e submissão não verificadas nesta revisão. |

O documento informa **19/09/2026** como prazo do entregável e **até 14/10/2026**
para a apresentação. A apresentação deve durar no máximo sete minutos, ser feita
por um integrante escolhido pelo professor e ser versionada e submetida no Blackboard.

O professor determina que a entrega avaliada é a disponível na **branch `main`
até a data limite**. Esta revisão está na branch de ajustes e não foi integrada
à `main`; sua publicação não altera nem comprova o conteúdo entregue no prazo.

## Entregas por data e requisitos do professor

As datas abaixo correspondem aos encontros solicitados no caderno. A existência
dos arquivos e dos registros históricos não comprova a data de submissão ao professor.

| Encontro | Solicitado no caderno | Implementação e registros disponíveis |
| --- | --- | --- |
| 26/08/2026 — Docker | Repositório da equipe e convite ao professor; Dockerfiles para Java, MySQL e Redis; build e execução isolada | Repositório e três Dockerfiles presentes; builds e testes isolados reexecutados em 06/10/2026, com resultados em `docs/validacao-2026-10-06.md`. |
| 02/09/2026 — Docker Compose | Integrar os três builds, configurar rede e volumes, iniciar o ambiente com um comando e testar a comunicação | Compose com três serviços, DNS interno, rede compartilhada e volumes nomeados; resposta integrada registrada anteriormente neste README. |
| 09/09/2026 — Kubernetes | Deployments e Services dos três serviços; aplicação no cluster; inspeção pelo K9s, métricas e eventuais CrashLoopBackOff | Manifestos reaplicados em 06/10/2026; três Pods prontos, métricas coletadas e inspeção de Pods/eventos pelo K9s. Nenhum CrashLoopBackOff observado. Persistência e recuperação da API possuem registros históricos. |

## Ajustes documentais de 06/10/2026

- Descrição da API alinhada ao código: `/health` verifica conexões TCP; não grava dados nem executa operações de negócio.
- Roteiro isolado da API corrigido para HTTP 503 quando os bancos estão inacessíveis; explicado o estado `unhealthy` nesse cenário.
- Registro Kubernetes organizado para separar os resultados históricos das tentativas com impedimentos e da conferência atual.
- Criado `docs/respostas-caderno.md` com seis respostas para os campos de decisão e pendências de preenchimento. O Word original permanece sem alteração; nomes e papéis aguardam confirmação.
- Preservados os nomes e as funções da equipe registrados neste repositório.
- Verificadas a configuração do Compose e a integridade do diff. Na conferência inicial, o Docker estava inacessível; após sua abertura, os testes isolados, Compose e Kubernetes foram reexecutados e as métricas coletadas, conforme `docs/validacao-2026-10-06.md`.
- Após leitura dos documentos gerais, acrescentados o contexto do produto, a dinâmica das sessões, os membros do time e os requisitos de Terraform, apresentação, prazos e branch de avaliação.

Esta revisão altera documentação. Os arquivos da API, Dockerfiles, Compose e
manifestos Kubernetes mantêm a implementação existente.

## Escopo do projeto

Este repositório contempla os encontros de 26/08, 02/09 e 09/09/2026:

- empacotamento isolado da API Java, do MySQL e do Redis;
- orquestração dos três serviços com Docker Compose;
- comunicação pelo DNS interno do Docker (`db` e `redis`);
- persistência estruturada por volumes nomeados.

A entrega de 09/09 inclui Kubernetes e K9s. O caderno enviado contém somente esses três encontros. Existe uma apresentação em `docs/mecaniQA-nuvem-OAT1-Salvador.pdf`; sua presença não comprova apresentação em aula.

A especificação geral da OAT 1 complementa o caderno e inclui Terraform e os
requisitos de apresentação detalhados acima. A ausência desses itens não deve
ser interpretada como uma entrega integral da OAT 1.

A API implementa `/health`: verifica conectividade TCP com MySQL e Redis e retorna HTTP 200 quando ambos estão acessíveis ou HTTP 503 quando alguma dependência está indisponível. Não executa consultas SQL, comandos Redis ou gravação de telemetria. Os testes de persistência registrados foram realizados diretamente nos bancos.

As respostas para os campos de decisão e as pendências de preenchimento do caderno estão em [respostas-caderno.md](docs/respostas-caderno.md).

## Equipe registrada no README - 26/08 (a confirmar)

- Matheus Espírito Santo dos Santos - Desenvolvedor Piloto
- Albert Santos Soares - Copiloto (Revisor de Lógica) e Analista de Qualidade (QA)
- Rafael Pires Araújo - Arquiteto de Software / Documentador
- Juan Pablo Barros Carvalho - Scrum Master

## Equipe registrada no README - 02/09 (a confirmar)

- Matheus Espírito Santo dos Santos - Desenvolvedor Piloto
- Rafael Pires Araújo - Copiloto
- Albert Santos Soares - Arquiteto de Software / Documentador
- Juan Pablo Barros Carvalho - Scrum Master
- QA - não preenchido no guia

Esses registros são informações preexistentes do repositório. O caderno enviado em 06/10/2026 tem a maioria dos papéis vazios e apresenta o nome Lucas Almeida Silva no primeiro encontro. Confirmar os participantes e seus papéis antes de preencher ou substituir nomes no caderno.

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
curl.exe -i http://localhost:8080/health
```

Resposta esperada no teste isolado, sem MySQL e Redis acessíveis: HTTP `503 Service Unavailable`.

```json
{"status":"DOWN","service":"mecaniqa-api","mysql":"DOWN","redis":"DOWN"}
```

A resposta demonstra que o servidor HTTP está funcionando, mas as dependências estão indisponíveis. Nesse teste, o health check do contêiner fica `unhealthy`, pois consulta o mesmo endpoint. Para obter HTTP 200 e os três componentes em `UP`, execute o ambiente integrado com Docker Compose. `EXPOSE` documenta a porta; a publicação no host é feita por `-p 8080:8080`.

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

### Teste integrado registrado anteriormente

Com os três contêineres ativos, foi executado:

```powershell
curl.exe http://localhost:8080/health
```

Resultado obtido:

```json
{"status":"UP","service":"mecaniqa-api","mysql":"UP","redis":"UP"}
```

Esse resultado registrado confirma simultaneamente que a API responde na porta publicada
`8080`, que os nomes `db` e `redis` são resolvidos pelo DNS interno e que as portas
dos dois serviços podem ser alcançadas pela API.

### Observações de escopo

- A verificação atual comprova conectividade TCP entre as camadas; operações de
  negócio, consultas SQL e comandos Redis não estão implementados na API.
- Volumes e PVCs configurados preservam dados armazenados pelos bancos quando reutilizados. A configuração sozinha não comprova um teste de gravação e recuperação; a evidência histórica do Kubernetes está em `docs/validacao-kubernetes.md`.
- As credenciais declaradas são exclusivas para o ambiente didático local e não
  devem ser usadas em produção.
- A remoção completa dos volumes com `docker compose down -v` apaga os dados e,
  por isso, não faz parte do procedimento normal de encerramento.

## 5. Entrega do Encontro 3 - Kubernetes (09/09/2026)

Branch: `entrega-kubernetes-09-09`. Piloto: Juan Pablo; copiloto: Matheus Santos,
conforme o registro anterior do repositório, a confirmar pela equipe. O caderno enviado não preenche esses papéis.

| Componente | Deployment / Service | Persistência | Acesso |
| --- | --- | --- | --- |
| API Java | api | Sem estado; não requer PVC | NodePort 30080 → porta 8080 |
| MySQL | mysql | mysql-data, 1 GiB em /var/lib/mysql | ClusterIP, mysql:3306 |
| Redis | redis | redis-data, 1 GiB em /data, AOF habilitado | ClusterIP, redis:6379 |

Os recursos ficam no namespace `mecaniqa`. Os Deployments mantêm uma réplica e
recriam Pods que falham. MySQL e Redis usam estratégia `Recreate` para evitar
instâncias concorrentes escrevendo no mesmo volume durante atualizações.
Cada contêiner tem requests e limits de CPU e memória. A readiness da API consulta
`/health` (conectividade TCP aos dois bancos); startup e liveness verificam sua
porta, evitando reinícios da API causados por indisponibilidade dos bancos.
O Secret contém uma senha exclusivamente didática. A API atual verifica TCP;
não autentica no MySQL nem executa operações de negócio.

### Cluster local reproduzível no Windows

Pré-requisitos: Docker Desktop em modo Linux, kubectl, Kind e K9s.
O script exige por padrão uma reserva de 8 GiB livres na unidade de
`LOCALAPPDATA`, onde fica o disco do Docker nesta máquina, para evitar a repetição
das falhas de armazenamento observadas. A reserva pode ser ajustada com
`-MinimumFreeDiskGB` se o armazenamento do Docker estiver configurado de outra forma.
As ferramentas desta execução estão em `.local/bin/` (ignoradas pelo Git).
Instalação em outra máquina: obtenha os binários Windows amd64 nas páginas
oficiais de [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/) e
[K9s](https://github.com/derailed/k9s/releases) e confira seus checksums.
Coloque Kind em `.local/bin/kind.exe` e K9s em `.local/bin/k9s/k9s.exe`.

Na raiz do projeto, execute:

```powershell
./scripts/deploy-local.ps1
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
kubectl --context kind-mecaniqa get nodes
curl.exe --fail http://localhost:18080/health
.local/bin/k9s/k9s.exe --kubeconfig .local/kubeconfig --context kind-mecaniqa -n mecaniqa --readonly
```

O script constrói as três imagens, cria o cluster `mecaniqa` definido em
`infra/kind.yaml`, carrega as imagens no runtime do Kind, valida no servidor,
aplica os manifestos e aguarda os rollouts. O kubeconfig fica apenas em `.local/`.
A porta 18080 do computador encaminha para o NodePort 30080, sem depender de
port-forward. O bind em localhost é adequado à demonstração nesta máquina.
As imagens mantêm a tag `encontro1` dos Dockerfiles já existentes; depois de
reconstruí-las, carregue-as novamente e reinicie os Deployments para atualizar Pods.

Resposta esperada:

```json
{"status":"UP","service":"mecaniqa-api","mysql":"UP","redis":"UP"}
```

### Aplicação manual em outro cluster

Confira o contexto antes de aplicar. Publique as imagens em um registry acessível
aos nós e ajuste `image` nos manifestos, ou carregue-as no runtime de todos os nós.
O cluster precisa de uma StorageClass padrão para provisionar os PVCs.

```powershell
kubectl config current-context
kubectl get storageclass
kubectl apply -f k8s/namespace.yaml
kubectl apply --dry-run=server -f k8s/
kubectl apply -f k8s/
kubectl -n mecaniqa rollout status deployment/mysql --timeout=300s
kubectl -n mecaniqa rollout status deployment/redis --timeout=300s
kubectl -n mecaniqa rollout status deployment/api --timeout=300s
kubectl -n mecaniqa get deploy,pods,svc,pvc
```

A API fica disponível em `http://<IP-acessível-do-nó>:30080/health` se a rede
permitir. Em nuvem com controlador de LoadBalancer, o Service da API pode usar
`type: LoadBalancer`; consulte o endereço em `kubectl -n mecaniqa get svc api`.
MySQL e Redis permanecem internos.

### Inspeção e diagnóstico

No K9s, use `:deploy`, `:pods`, `:svc`, `:pvc` e `:events`; selecione um Pod e use
`l` para logs e `d` para detalhes. Use `:q` para sair. CPU e memória dependem de
Metrics Server disponível; ausência de métricas não significa consumo zero.
Veja os [comandos oficiais do K9s](https://k9scli.io/topics/commands/).

```powershell
kubectl -n mecaniqa get endpointslices
kubectl -n mecaniqa get events --sort-by=.metadata.creationTimestamp
kubectl -n mecaniqa logs deployment/api --tail=50
kubectl -n mecaniqa describe pods
kubectl -n mecaniqa top pods
```

Para `CrashLoopBackOff`, examine também `kubectl logs <pod> --previous -n mecaniqa`.
Para PVC `Pending`, verifique StorageClass e eventos; para `ImagePullBackOff`,
confira imagem, runtime e acesso ao registry. Os probes seguem o comportamento
explicado na [documentação Kubernetes](https://kubernetes.io/docs/concepts/workloads/pods/probes/).

Os PVCs sobrevivem à recriação dos Pods. No Kind, seus dados ficam no contêiner
do nó: remover o cluster também remove essa persistência local. Não exclua o
namespace ou os PVCs para encerrar uma demonstração que deve preservar dados.

As evidências da execução ficam em `docs/validacao-kubernetes.md`.

### Validação executada em 06/10/2026

- Docker Engine 29.7.2 acessível; três imagens construídas e serviços testados isoladamente.
- Compose iniciado com build e espera por saúde; API, MySQL e Redis saudáveis e `/health` com HTTP 200.
- Manifestos Kubernetes validados no servidor e reaplicados ao contexto `kind-mecaniqa`; três Pods `1/1 Running` e PVCs `Bound`.
- Metrics Server 0.8.1 instalado no Kind local; API de métricas disponível e CPU/memória exibidas no K9s.
- Pods e eventos inspecionados no K9s; nenhum Pod em `CrashLoopBackOff` no momento da inspeção.

Os comandos, resultados e limites desta validação estão em
[validacao-2026-10-06.md](docs/validacao-2026-10-06.md).
