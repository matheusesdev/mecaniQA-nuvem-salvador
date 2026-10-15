# Roteiro de explicação — 14/10/2026

Use como apoio para explicar com suas palavras. Duração sugerida: 5–7 minutos.
Leia o registro de validação antes de gravar para relatar somente os testes
realmente executados. Confirme com a equipe quem apresenta e os papéis do dia.

## 1. Problema e objetivo — 40 segundos

Mostrar o trecho de 14/10 do caderno e a branch no repositório.

“Nesta etapa precisávamos conectar o Grafana ao Prometheus e entregar quatro
visualizações: CPU, memória, erro e sucesso. O simulador Python e a coleta pelo
Prometheus já haviam sido preparados na etapa anterior. Criamos uma branch para
organizar essa mudança e versionamos a configuração para reproduzir o ambiente.”

## 2. De onde vêm os dados — 1 minuto

Mostrar `simulator/app.py`: definições dos contadores, `process_reading()` e
`start_http_server(8000)`. Mostrar o job `iot-simulator` em `k8s/prometheus.yaml`.

“O simulador processa leituras sintéticas. Quando uma leitura é válida, incrementa
o contador de sucesso. Quando é rejeitada, incrementa o contador de erro.
A biblioteca expõe os números em /metrics e o Prometheus os coleta a cada 15
segundos. Uma falha elétrica encontrada no veículo continua sendo um diagnóstico
processado com sucesso. Ela é diferente de um erro no nosso software.”

Verificação de compreensão: por que ler um valor inválido não deve incrementar
sucesso? Onde o `finally` garante que a métrica de leituras em processamento
volte ao valor correto mesmo quando ocorre uma exceção?

## 3. Como o Grafana foi implantado — 1 minuto

Mostrar `k8s/grafana.yaml`, depois os dois YAMLs em `grafana/provisioning/`.

“O Deployment mantém o Grafana em execução; o Service fornece o acesso interno;
o PVC preserva os dados da instância. Configuramos probes e limites de recursos.
A senha fica em um Secret do cluster. A fonte de dados aponta para o Service do
Prometheus dentro do Kubernetes. O navegador não coleta diretamente do Python:
o Grafana consulta as séries que o Prometheus já armazenou.”

Verificação de compreensão: por que o endereço da fonte de dados é o DNS interno
do Prometheus, e não `localhost:9090`? `localhost` dentro do Grafana apontaria para
o próprio contêiner do Grafana.

## 4. Mostrar os quatro gráficos — 2 minutos

Abrir a pasta **MecaniQA OAT 2** no Grafana e alternar pelos quatro dashboards.

- CPU: “Transformamos os segundos de CPU acumulados em taxa com `rate()` e
  multiplicamos por 100. Cem por cento corresponde a um núcleo. Esse gráfico
  mede o processo Python, não o computador inteiro.”
- Memória: “Usamos a memória residente, ou RSS. É um valor instantâneo em bytes,
  então não aplicamos `rate()`. O Grafana formata o tamanho para leitura.”
- Erro: “Mostramos rejeições por segundo. Zero com coleta funcionando significa
  que não observamos erros. Sem dados não significa zero erros.”
- Sucesso: “Somamos as taxas de leituras válidas dos dois tipos de sensor. Isso
  mostra o ritmo de processamento; o total acumulado sozinho esconderia uma
  queda recente.”

Verificação de compreensão: se reiniciarmos o simulador, o contador volta a
zero. `rate()` trata a reinicialização do contador; uma subtração manual simples
poderia produzir um valor negativo incorreto.

## 5. Reprodutibilidade e validação — 1 minuto

Mostrar os quatro JSONs em `grafana/dashboards/`, o script
`scripts/sync-grafana-config.ps1` e `docs/validacao-2026-10-14.md`.

“As definições dos gráficos estão em JSON. O script gera os ConfigMaps a partir
dos arquivos, assim a implantação carrega a mesma configuração que está no Git.
Conferimos a coleta, a conexão da fonte de dados e os quatro dashboards.
Os resultados observados e as limitações estão documentados. O próximo encontro
trata dos alarmes e do HPA; o foco de hoje é monitoramento visual.”

Se alguma verificação do ambiente ainda estiver pendente, explique a pendência
conforme o registro, em vez de dizer que ela passou.

## Autoria e uso de apoio

O roteiro não é evidência de que cada integrante escreveu o código ou participou
dos testes. Se o professor perguntar sobre ferramentas utilizadas, descreva o
apoio recebido de forma transparente. Demonstre domínio abrindo a consulta de
um painel, explicando a unidade e relacionando o resultado com a métrica Python.
