# Validação da entrega de 09/09/2026

Branch criada: `entrega-kubernetes-09-09`.

## Estado mais recente — retomada de 10/09/2026

### Validação concluída

Com 4,94 GiB livres, o script foi executado com `-MinimumFreeDiskGB 4`. As três
imagens foram reconstruídas a partir do cache e o cluster Kind `mecaniqa` foi
criado com Kubernetes v1.34.0. A carga conjunta das imagens ficou sem saída por
tempo prolongado e foi interrompida; a carga individual concluiu para API,
MySQL e Redis. O script passou a carregar cada imagem individualmente.

Os dez recursos passaram por `kubectl apply --dry-run=server` e foram aplicados:
Namespace, Secret, três Services, dois PVCs e três Deployments. Os três rollouts
concluíram. Todos os Pods ficaram `1/1 Running`, os PVCs `Bound` com 1 GiB e os
Services internos obtiveram EndpointSlices. A API ficou exposta em NodePort
30080, acessível no host pela porta 18080.

Resultado do acesso externo:

```json
{"status":"UP","service":"mecaniqa-api","mysql":"UP","redis":"UP"}
```

O Redis retornou `PONG`, e `SELECT 1` no banco `mecaniqa` retornou `1`. Para a
prova de persistência, foi gravado `kubernetes-ok` na chave Redis
`validacao:persistencia` e na tabela MySQL `validacao_k8s`. Depois de reiniciar
os dois Deployments e aguardar os rollouts, ambos devolveram `kubernetes-ok`.

O auto-healing foi validado excluindo o Pod `api-df7f9b654-98dwz`. O Deployment
criou `api-df7f9b654-kjbp9`, que ficou pronto, e `/health` continuou retornando
todos os componentes como `UP`.

K9s v0.51.0 foi aberto com o contexto `kind-mecaniqa`, namespace `mecaniqa`,
comando `pods` e modo `--readonly`. A tela mostrou os três Pods `1/1 Running` e
foi encerrada normalmente com `:q`. As advertências de readiness da API e startup
do MySQL nos eventos ocorreram durante a inicialização/recriação e foram seguidas
por rollouts bem-sucedidos.

Na nova tentativa solicitada, o Docker respondeu a `docker info`, mas a proteção
do script interrompeu a execução com 3,27 GiB livres em C:, abaixo da reserva
configurada de 8 GiB. Nenhum build ou aplicação foi iniciado por essa execução.

O Docker voltou ao estado `running`, o disco EXT4 foi confirmado em modo `rw`
e o contêiner preexistente `degrader_api` voltou a ficar ativo. Não foi necessário
executar o encerramento forçado dos processos, que havia sido rejeitado.

O script de implantação foi retomado: API e MySQL concluíram o build. A imagem
Redis também foi registrada no Docker, mas a execução foi interrompida durante
sua exportação/descompactação, antes da criação do cluster. O build Redis deve
ser repetido para confirmar sua conclusão na próxima execução.

O espaço livre caiu de 1.773.928.448 para 747.712.512 bytes (cerca de 713 MiB).
A execução foi interrompida com Ctrl+C para evitar uma nova falha de escrita.
`kind get clusters` confirmou que não há cluster criado. Aplicação dos manifestos,
testes de conectividade/persistência e inspeção no K9s continuam pendentes.

O script agora verifica uma reserva operacional de 8 GiB livres na unidade de
`LOCALAPPDATA` antes dos builds, da criação do cluster e da carga de imagens.
Esse valor é uma margem para esta máquina, não um requisito universal do Kind;
pode ser ajustado pelo parâmetro `MinimumFreeDiskGB`. O parser PowerShell e
`git diff --check` aceitaram a alteração. O histórico abaixo registra as tentativas
anteriores e não substitui este estado mais recente.

## Implementação

- Namespace `mecaniqa`, três Deployments e três Services.
- API via NodePort 30080, mapeado para localhost:18080 pelo Kind.
- MySQL e Redis via DNS interno, Services ClusterIP e PVCs de 1 GiB.
- Probes, requests/limits e estratégia Recreate para os bancos.
- Script `scripts/deploy-local.ps1` para construir, carregar, aplicar e validar.

## Execução e impedimento

O kubectl v1.34.1 está instalado, mas não havia contexto configurado.
Kind v0.33.0 e K9s v0.51.0 foram baixados dos repositórios oficiais para
`.local/bin/`, com hashes SHA256 conferidos antes da execução.
A imagem `mecaniqa-api:encontro1` foi construída com sucesso.

A construção do MySQL e a criação do cluster Kind falharam com erros de
entrada/saída no armazenamento do Docker:

```text
failed to commit snapshot ... commit failed: input/output error
write /var/lib/desktop-containerd/daemon/io.containerd.metadata.v1.bolt/meta.db: input/output error
```

No diagnóstico, a unidade C: tinha 229.998.592 bytes livres (cerca de 219 MiB).
`docker system df` também falhou ao ler blobs com `input/output error`.
Havia um contêiner existente, `degrader_api`, em execução.
Não foram removidos dados nem reiniciado o Docker para evitar interromper esse
contêiner sem necessidade e sem resolver antes a falta de espaço.

O parser PowerShell aceitou o script e `git diff --check` não apontou erros.
A renderização local com `kubectl kustomize` aceitou os YAMLs e produziu os dez
recursos esperados: Namespace, Secret, três Services, dois PVCs e três Deployments.
Isso verifica a leitura/renderização, não substitui validação pelo servidor.
O K9s foi iniciado, mas registrou `No API server connection` e ausência de
`.local/kubeconfig`; a instância de diagnóstico foi encerrada.
Não houve aplicação em cluster, teste HTTP externo, teste de persistência,
inspeção de Pods no K9s nem coleta de métricas. Resultados esperados no README
não representam testes executados nesta etapa.

## Retomada

Na tentativa seguinte, a reinicialização normal autorizada foi executada com
`docker desktop restart --timeout 120`, mas terminou com `context deadline
exceeded`. O Docker permaneceu em `starting`, sem API utilizável. Durante essa
tentativa, C: apresentou 3.882.045.440 bytes livres (cerca de 3,6 GiB).
Os logs WSL mostraram falhas de leitura em `loop1`, crash de `initd` e falha ao
desanexar o disco `sdd`. Esses registros não permitem afirmar recuperação dos dados.

A proposta de parar Docker, terminar apenas a distribuição WSL `docker-desktop`
e iniciar novamente foi rejeitada pela revisão automática de aprovação, por
risco ao serviço existente e aos dados diante dos erros de disco. Essa sequência
não foi executada. A recuperação exige aprovação específica ou intervenção local.
O estado do `degrader_api` após a reinicialização não pôde ser confirmado pela API.

Nova tentativa após a solicitação de prosseguir: C: apresentava 793.198.592
bytes livres (cerca de 756 MiB), mas o script falhou já no build da API com o
mesmo erro no `meta.db`. O diagnóstico via `dmesg` confirmou journal EXT4
abortado e `Remounting filesystem read-only` no disco de dados do Docker.
Assim, liberar espaço por si só ainda não restabeleceu as gravações.
O contêiner existente `degrader_api` usa a imagem `autotruck-api-api` e política
de reinício `always`; reiniciar Docker interromperia temporariamente esse serviço.
Nenhum cluster Kind foi encontrado e nenhum manifesto foi aplicado nesta tentativa.

Libere espaço suficiente para as imagens e o disco virtual do Docker. Se os
erros de entrada/saída persistirem, recupere o funcionamento do Docker Desktop
antes de continuar. Na raiz do repositório:

```powershell
./scripts/deploy-local.ps1
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
kubectl -n mecaniqa get deploy,pods,svc,pvc
kubectl -n mecaniqa exec deployment/redis -- redis-cli ping
curl.exe --fail http://localhost:18080/health
.local/bin/k9s/k9s.exe --kubeconfig .local/kubeconfig --context kind-mecaniqa -n mecaniqa --readonly
```

Para demonstrar persistência, grave uma chave Redis e um registro SQL de teste,
reinicie os Deployments dos bancos com `kubectl rollout restart`, aguarde os
rollouts e confira os mesmos valores. Para demonstrar recuperação da API,
exclua apenas seu Pod de teste e confira a nova réplica e `/health` novamente.
Use `:pods`, `:svc`, `:pvc`, `:events`, logs (`l`) e descrição (`d`) no K9s.
Métricas de CPU/memória exigem Metrics Server no cluster.
