# Escalonamento alarmes e teste de estresse

Entrega da primeira sessão de 21/10/2026 da equipe Salvador. Esta etapa acrescenta HPA e quatro regras ativas ao Grafana, mantendo os quatro dashboards da sessão de 14/10. O teste verifica escala, disparo e recuperação em um ambiente acadêmico local.

## Contexto e decisões preservadas

Foram lidos integralmente os cadernos OAT 1 Tutoriais, OAT 2 Monitorando a Continuidade e OAT 2 Escalabilidade e IoT fornecidos pelo aluno. As instruções de publicar na main e no Blackboard descrevem a avaliação; este trabalho prepara duas branches locais conforme solicitado, sem submissão externa.

| Sessão | Decisão registrada e relação com esta entrega |
| --- | --- |
| 26/08 | Java em imagem Temurin Alpine, EXPOSE e processo principal; Dockerfiles preservados. |
| 02/09 | DNS de serviços, rede interna e volumes; nenhuma remoção de dados. |
| 09/09 | Deployments para recuperação, bancos internos e API externa; namespace e serviços preservados. |
| 07/10 | prometheus-client, /metrics, coleta a cada 15 s; falhas do veículo separadas de rejeições da aplicação. |
| 14/10 | Exatamente quatro dashboards, datasource por provisioning, rate em contadores; mantidos. |
| 21/10 primeira sessão | Quatro alarmes, HPA 1 a 5 réplicas, CPU 70% e memória 80% dos requests, estabilização de redução de 300 s. |
| 21/10 segunda sessão | Runbooks e SLA 99,9%, SLO 99,95%, SLI externo, RTO 30 min e RPO 15 min; documentação na branch seguinte. |

Papéis em ambas as sessões de 21/10: piloto Juan Pablo Barros Carvalho; copiloto Matheus Espírito Santo dos Santos; QA Rafael Pires Araújo; Scrum Master Albert Santos Soares. Arquiteto não preenchido no caderno.

## Implementação

O HPA em `k8s/simulator-hpa.yaml` usa `autoscaling/v2` e seleciona a maior recomendação entre CPU e memória. Os requests continuam em 50m e 64Mi; os limites continuam em 250m e 128Mi. O Deployment deixa de fixar réplicas para não sobrescrever a decisão do HPA em reaplicações. A memória do processo não é idêntica ao working set usado pelo Metrics Server.

O novo Service headless `simulator-metrics` permite descoberta DNS dos IPs de cada Pod. O Prometheus deixa de coletar um endereço balanceado, o que misturaria contadores de réplicas diferentes. Não é necessário conceder permissões da API Kubernetes ao Prometheus.

As regras em `grafana/provisioning/alerting/alerts.yaml` são provisionadas por ConfigMap, avaliadas a cada 20 s e mantêm a condição por dois minutos antes de disparar. JSON foi utilizado como sintaxe válida de YAML para preservar o modelo das expressões. Ausência de dados e falha na consulta aparecem como NoData/Error, sem serem confundidas com recuperação. As regras estão ativas; não foi configurado envio de notificações externas.

| Regra | Condição sustentada por dois minutos |
| --- | --- |
| CPU | Maior CPU de processo por réplica / 0,25 núcleo > 80%. Equivale a mais de 200m, não a 80% de um núcleo. |
| Memória | Maior RSS por réplica > 102,4 MiB, 80% do limite de 128Mi. |
| Erro | Soma das taxas de rejeição / soma das taxas de tentativas > 5%, com pelo menos vinte tentativas na janela de 1 min. |
| Sucesso | Soma das taxas de sucesso < 80% da soma das taxas alvo positivas. A taxa alvo indica carga configurada, não tráfego externo observado. |

O uso de máximo nos alarmes de infraestrutura evita esconder uma réplica saturada na média. As taxas da aplicação somam réplicas depois de aplicar rate individualmente.

## Reprodução local

Pré-requisitos: Docker Desktop Linux, kubectl, Kind em `.local/bin/kind.exe`, Python e Edge. O cluster se chama `mecaniqa`; o kubeconfig fica em `.local/kubeconfig`.

```powershell
python -m venv .local/venv
.local/venv/Scripts/python.exe -m pip install -r simulator/requirements.txt pyyaml playwright
.local/venv/Scripts/python.exe -m unittest discover -s simulator -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare-autoscaling.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy-local.ps1
$env:KUBECONFIG = Join-Path (Get-Location) '.local/kubeconfig'
kubectl --context kind-mecaniqa -n mecaniqa get hpa
```

Se o cluster ainda não existir, execute primeiro o deploy, depois prepare-autoscaling. O HPA ficará aguardando a Metrics API até ela estar disponível. O script de preparação usa Metrics Server 0.8.1 e permite certificado não confiável de kubelet apenas no Kind local. Esse ajuste não deve ser utilizado em produção.

Abra os port-forwards em terminais separados, mantendo-os ativos durante o teste:

```powershell
kubectl --context kind-mecaniqa -n mecaniqa port-forward service/prometheus 9090:9090
kubectl --context kind-mecaniqa -n mecaniqa port-forward service/grafana 3000:3000
```

Valide o provisionamento e execute o teste na raiz:

```powershell
.local/venv/Scripts/python.exe scripts/validate-autoscaling.py
.local/venv/Scripts/python.exe scripts/stress-test.py
```

O script verifica as APIs antes de alterar o simulador, solicita 100 leituras/s por réplica, 10 ms de CPU por tentativa, 80Mi de memória adicional e 20% de leituras inválidas. A memória adicional é limitada a 80Mi e as páginas são tocadas para produzir RSS real. A taxa efetiva pode ficar abaixo da solicitada por causa do limite de CPU; esse é o cenário deliberado do alarme de sucesso. Os erros não representam falhas dos veículos.

A injeção ocorre dentro do gerador sintético, via configuração do Deployment, e se replica com os Pods. Portanto a demanda cresce com o número de réplicas: este experimento comprova os controles, não dimensiona a capacidade de um serviço sob tráfego externo constante. Não há endpoint de ingestão IoT na API Java.

O script salva amostras UTC, estados das regras, status do HPA, targets do Prometheus, eventos, logs e capturas reais. Aceita a fase de estresse somente com as quatro regras firing e mais de uma réplica. No bloco finally restaura a configuração original, espera a estabilização e exige uma réplica pronta e quatro regras inactive. O resultado só é aprovado quando ambas as fases passam. Em interrupção abrupta, confira e restaure manualmente as variáveis antes de repetir.

## Evidência e limites

Os registros ficam em `docs/evidencias/2026-10-21-estresse/`. A data da pasta identifica a sessão acadêmica; os timestamps registram a execução real. O relatório de validação informa os resultados observados, sem retroagir a data do teste.

O PDF final de apresentação, seu modelo e a submissão no Blackboard pertencem à avaliação geral da OAT 2 e não foram solicitados como entrega destas duas sessões. A integração na main também exige uma ação posterior do responsável.

## Referências técnicas

- [HPA e métricas de recursos](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Comportamento e estabilização do HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/)
- [Services headless](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [Provisionamento de alertas Grafana](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/)
