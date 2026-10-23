# Validação das entregas de 21 de outubro

Sessão acadêmica de 21/10/2026; execução local em 23/10/2026, horário da Bahia. A primeira branch implementa o HPA, os alarmes e o teste. A segunda acrescenta os runbooks e o acordo operacional. Os registros UTC nos arquivos permitem reconstruir a sequência real.

## Verificações da implementação

| Verificação | Resultado observado |
| --- | --- |
| Testes Python | Oito testes passaram, incluindo injeção desativada por padrão, limites de consumo e contagem de rejeições controladas. |
| Build | Imagens construídas e carregadas no Kind; simulador usa autoscaling-v2. |
| Manifestos | Todos os recursos de k8s passaram por dry-run no servidor e foram aplicados no contexto kind-mecaniqa. |
| Metrics Server | Versão 0.8.1, APIService Available, top pods com CPU e memória disponíveis. Ajuste de TLS limitado ao Kind local. |
| Implantação | API, MySQL, Redis, simulador, Prometheus e Grafana disponíveis; PVCs Bound. |
| Saúde da API | HTTP 200, status UP, mysql UP e redis UP. |
| Grafana e datasource | Grafana 12.2.0 com database ok; datasource Prometheus com status OK. |
| Dashboards e regras | Exatamente quatro dashboards e quatro regras ativas, sem pausa. As quatro consultas retornaram amostras. |
| ConfigMaps | Regeneração não alterou o hash do arquivo, confirmando geração determinística. |
| Sintaxe | YAMLs carregados com PyYAML; scripts PowerShell sem erros no parser; Python compilado; git diff --check sem erros. |

## Escala e alarmes

O HPA foi observado aumentando de uma para duas e depois cinco réplicas. Durante o estresse, o uso chegou a aproximadamente 500% do request de CPU de 50m por réplica, coerente com o limite de 250m, e aproximadamente 158% do request de memória de 64Mi. Os quatro estados chegaram simultaneamente a firing, depois das janelas de avaliação.

Após restaurar as variáveis originais, os quatro alarmes voltaram a inactive e o HPA reduziu de cinco para duas e depois uma réplica pronta. A redução ocorreu em etapas, respeitando a estabilização de 300 s em cada recomendação. O [resultado do teste](evidencias/2026-10-21-estresse/resultado.json) registra as duas condições de aprovação: stress_passed e recovery_passed.

Capturas do estresse: [quatro alarmes](evidencias/2026-10-21-estresse/estresse-alarmes.png), [CPU](evidencias/2026-10-21-estresse/estresse-cpu.png), [Memória](evidencias/2026-10-21-estresse/estresse-memoria.png), [Erro](evidencias/2026-10-21-estresse/estresse-erro.png) e [Sucesso](evidencias/2026-10-21-estresse/estresse-sucesso.png). A [captura da recuperação](evidencias/2026-10-21-estresse/recuperacao-alarmes.png) mostra o retorno das regras ao estado normal. Os quatro dashboards também foram capturados após a recuperação.

O arquivo [configuração validada](evidencias/2026-10-21-estresse/configuracao-validada.json) contém respostas reais de saúde, datasource, regras e consultas. As [amostras](evidencias/2026-10-21-estresse/amostras.json) registram HPA, réplicas prontas, regras, horários e targets. O [inventário e eventos](evidencias/2026-10-21-estresse/recursos.txt) registra SuccessfulRescale, e o [log do simulador](evidencias/2026-10-21-estresse/simulator-stress.log) contém rejeições da injeção controlada. Nenhum Secret foi incluído nesses arquivos.

O [log do Grafana](evidencias/2026-10-21-estresse/grafana-alarmes.log) complementa os estados das regras com os registros do avaliador e do notificador local. Não foi configurado envio para pessoas ou canais externos.

## Ajustes encontrados na execução

O Docker estava parado no início; o cluster existente foi retomado. O Python disponível não tinha prometheus-client, então foi criado um ambiente virtual local e instaladas as dependências do projeto e as ferramentas de validação.

O Grafana rejeitou o intervalo inicial de avaliação de 15 s por não ser múltiplo do scheduler de 10 s. O provisionamento foi corrigido para 20 s e o Grafana voltou a iniciar. Os limites e a condição sustentada por dois minutos foram mantidos. A captura da lista de regras exige aguardar seu carregamento e expandir a pasta, além de verificar o estado pela API.

## Limites de interpretação

O teste é sintético e injeta consumo e rejeições dentro de cada réplica do gerador; não é benchmark de ingestão HTTP e não determina capacidade real. CPU e RSS nos dashboards são agregados do processo Python; os alarmes de infraestrutura usam o máximo por réplica, e o HPA utiliza métricas de contêiner do Metrics Server.

SLA, SLO, RTO e RPO são as metas formalizadas pela equipe. Não foram demonstrados disponibilidade anual, monitoramento externo contínuo, backup fora da região nem restauração de dados. Não houve integração na main, push ou submissão no Blackboard.
