# MecaniQA Nuvem Salvador

Entrega da equipe Salvador para a OAT 1 de Docker, Docker Compose e Kubernetes.

## Escopo desta sessão

Este repositório contempla os encontros de 26/08, 02/09 e 09/09/2026:

- empacotamento isolado da API Java, do MySQL e do Redis;
- orquestração dos três serviços com Docker Compose;
- comunicação pelo DNS interno do Docker (`db` e `redis`);
- persistência estruturada por volumes nomeados.

A entrega de 09/09 inclui Kubernetes e K9s. Terraform e a apresentação final ficam para etapas posteriores.

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

## 5. Entrega do Encontro 3 - Kubernetes (09/09/2026)

Branch: `entrega-kubernetes-09-09`. Piloto: Juan Pablo; copiloto: Matheus Santos,
conforme o guia. Demais papéis não preenchidos no documento.

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
