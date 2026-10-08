# Entrega inicial de métricas IoT e Prometheus

## Objetivo e arquitetura

O simulador Python produz leituras sintéticas de temperatura do motor e do
sistema elétrico, valida e processa cada leitura localmente e publica métricas
Prometheus na porta 8000, caminho `/metrics`. No namespace `mecaniqa`, um Service
ClusterIP direciona o tráfego ao simulador e o Prometheus coleta o endpoint a
cada 15 segundos. O Prometheus expõe sua própria interface na porta 9090 e
persiste a TSDB em PVC.

A coleta do simulador é estática pelo DNS do Service
`simulator.mecaniqa.svc.cluster.local:8000`. Ela atende a configuração desta
entrega com uma réplica. Um Service de balanceamento não coleta individualmente
cada Pod, portanto não se afirma coleta por réplica quando houver escala.

Não há envio de telemetria para a API Java, MySQL ou Redis. O tempo medido é
somente o processamento local e não representa latência de rede. A métrica de
taxa alvo representa a configuração, não a taxa efetivamente observada.

## Arquivos

| Arquivo | Função |
| --- | --- |
| `simulator/app.py` | Gera e valida leituras, controla picos, mede o processamento local, expõe métricas e trata SIGTERM/SIGINT. |
| `simulator/test_app.py` | Testes unitários de leituras, falhas simuladas, rejeições, métricas e configuração de picos. |
| `simulator/requirements.txt` | Dependências Python com versões fixas. |
| `simulator/Dockerfile` | Imagem Python 3.13 slim executada sem root. |
| `simulator/.dockerignore` | Exclui bytecode, cache e testes da imagem. |
| `k8s/simulator.yaml` | Deployment de uma réplica e Service ClusterIP do simulador. |
| `k8s/prometheus.yaml` | ConfigMap de scrape, PVC de dados, Deployment e Service ClusterIP do Prometheus. |
| `scripts/deploy-local.ps1` | Build e carga das imagens no Kind, aplicação dos manifestos, espera pelos rollouts e verificação preexistente da API e dos bancos. |
| `docs/validacao-2026-10-07.md` | Evidências, resultado dos testes e verificações pendentes da execução datada. |

## Dependências e pré-requisitos

- Python 3.13 ou compatível para execução local; `prometheus-client==0.22.1`
  fornece a instrumentação e `tzdata==2025.2` disponibiliza
  `America/Sao_Paulo` também em sistemas sem banco de fusos horário do sistema.
- Docker Desktop em modo Linux, Kind e kubectl para a implantação local.
- Cluster Kind chamado `mecaniqa`, contexto `kind-mecaniqa`, namespace
  `mecaniqa` e armazenamento provisionável por StorageClass padrão.
- O script usa `.local/kubeconfig`; confirme que o arquivo existe e contém o
  contexto antes de executar o deploy.
- Para validação da aplicação do lado do servidor é necessário um cluster
  acessível e as imagens do simulador disponíveis no Kind.

O Prometheus usa `prom/prometheus:v3.5.0`. A retenção é sete dias e há limite de
4 GB para dados em PVC de 5 GiB, deixando espaço para overhead e arquivos
auxiliares da TSDB.

## Testes, construção e execução isolada

Na raiz do repositório, rode os testes:

```powershell
python -m unittest discover -s simulator -v
```

Construa a imagem:

```powershell
docker build -t mecaniqa-simulator:metrics-v1 ./simulator
```

Execute no modo normal e consulte `/metrics`:

```powershell
docker run --rm --name mecaniqa-simulator -p 8000:8000 mecaniqa-simulator:metrics-v1
curl.exe http://localhost:8000/metrics
```

Para testar pico contínuo numa execução separada:

```powershell
docker run --rm --name mecaniqa-simulator-peak -p 8000:8000 `
  -e READINGS_PER_SECOND=1 -e PEAK_MULTIPLIER=5 -e PEAK_MODE=always `
  mecaniqa-simulator:metrics-v1
```

Os valores padrão são `READINGS_PER_SECOND=1`, `PEAK_MULTIPLIER=5` e
`PEAK_MODE=scheduled`. A taxa e o multiplicador precisam ser números finitos
positivos. Os modos aceitos são `scheduled`, `always` e `off`. No modo
`scheduled`, o multiplicador fica ativo por dez minutos a partir de 08h e 17h,
no fuso `America/Sao_Paulo`; fora dessas janelas aplica-se a taxa normal.

## Deploy e acesso

O script existente verifica o espaço em disco, constrói as imagens originais e a
imagem `mecaniqa-simulator:metrics-v1`, preserva a criação ou exportação do
kubeconfig do Kind, carrega as imagens, valida os manifestos no servidor,
aplica-os e aguarda os Deployments antigos e novos. A verificação final de
`/health` continua conferindo a API e seus bancos. Após aplicar, o script reinicia
os Deployments do simulador e do Prometheus para usar a imagem reconstruída com
a mesma tag e eventuais alterações no ConfigMap.

```powershell
./scripts/deploy-local.ps1
kubectl --context kind-mecaniqa -n mecaniqa get deploy,pods,svc,pvc
kubectl --context kind-mecaniqa -n mecaniqa port-forward service/prometheus 9090:9090
```

Com o port-forward ativo, acesse `http://localhost:9090`. Para reconstruir a
imagem usando a mesma tag, carregue a imagem atualizada no nó Kind e reinicie o
Deployment para recriar os Pods:

```powershell
docker build -t mecaniqa-simulator:metrics-v1 ./simulator
kind load docker-image --name mecaniqa mecaniqa-simulator:metrics-v1
kubectl --context kind-mecaniqa -n mecaniqa rollout restart deployment/simulator
```

Depois de atualizar `prometheus.yml` no ConfigMap, o Prometheus precisa ser
reiniciado para ler a configuração:

```powershell
kubectl --context kind-mecaniqa -n mecaniqa apply -f k8s/prometheus.yaml
kubectl --context kind-mecaniqa -n mecaniqa rollout restart deployment/prometheus
```

## Métricas expostas

Todas as métricas do simulador usam apenas `sensor_type` com valores limitados
`temperature` e `electrical`; não há rótulos de veículo, dispositivo ou timestamp.

| Métrica | Tipo | Significado |
| --- | --- | --- |
| `iot_readings_total{sensor_type}` | Counter | Leituras válidas processadas. |
| `iot_sensor_faults_total{sensor_type}` | Counter | Falhas automotivas simuladas, separadas de erros da aplicação. |
| `iot_sensor_value{sensor_type}` | Gauge | Valor da última leitura processada. |
| `iot_processing_errors_total` | Counter | Erros de processamento e rejeições de leitura inválida. |
| `iot_processing_seconds` | Histogram | Duração do processamento local, sem incluir ou alegar latência de rede. |
| `iot_readings_in_progress` | Gauge | Leituras em processamento, restaurado a zero após sucesso ou erro. |
| `iot_peak_active` | Gauge | Indicador 0/1 de que a janela de pico está ativa. |
| `iot_target_readings_per_second` | Gauge | Taxa alvo configurada, não uma medição de taxa efetivamente observada. |

## Consultas PromQL

Estado do scrape:

```promql
up{job="iot-simulator"}
```

Total acumulado de leituras válidas:

```promql
sum(iot_readings_total)
```

Taxa de leituras válidas por segundo (aguarde amostras suficientes; a janela
deve conter pelo menos duas amostras):

```promql
sum(rate(iot_readings_total[1m]))
```

Falhas simuladas por tipo:

```promql
sum by (sensor_type) (rate(iot_sensor_faults_total[5m]))
```

Valor mais recente da temperatura:

```promql
iot_sensor_value{sensor_type="temperature"}
```

## Limitações e evoluções futuras

- É uma carga sintética local, com uma réplica e scrape estático pelo Service.
  Não representa nem comprova capacidade para milhares de sensores reais
  simultâneos.
- Não há Grafana, broker de mensagens, autenticação de dispositivos ou
  autoscaling nesta etapa.
- A coleta por Service não descobre individualmente múltiplas réplicas.
- Leituras e falhas são simuladas e processadas dentro do contêiner; não existe
  ingestão ou persistência de telemetria nos serviços da API.

## Decisões — Fatos, Questões e Ideias

### Fatos

- A API atual implementa `/health` para verificar conexões TCP com MySQL e
  Redis; não é um endpoint de ingestão de telemetria.
- O Kind local existente usa namespace `mecaniqa`, e o fluxo de deploy
  existente preserva verificações de espaço, bancos e API.
- A coleta por DNS de Service é apropriada para a réplica única configurada.

### Questões

- Qual frequência e volume de amostras reais seriam necessários para uma
  futura prova de carga representativa?
- A expansão futura exigirá scrape por Pod via descoberta Kubernetes, ou outra
  arquitetura de ingestão?
- Quais limites de retenção e capacidade deverão ser definidos para ambientes
  além da demonstração local?

### Ideias

- Avaliar Grafana para dashboards e alertas em uma etapa futura.
- Avaliar broker, autenticação e ingestão segura antes de conectar dispositivos
  reais.
- Estudar descoberta por Pod e autoscaling somente após definir uma carga e
  objetivos operacionais representativos.
