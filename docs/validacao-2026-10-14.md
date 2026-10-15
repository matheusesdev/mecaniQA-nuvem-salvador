# Validação da entrega — 14/10/2026

Branch de implementação: `entrega-oat2-14-10-grafana`, a partir de
`e9b75b2` da `main`. Ambiente: Windows, Docker Desktop Linux, Docker Engine
29.4.2, Kind 0.30.0 com checksum oficial verificado e nó Kubernetes 1.34.0
declarado em `infra/kind.yaml`.

## Verificações locais concluídas

| Verificação | Resultado observado |
| --- | --- |
| Testes existentes do simulador | Seis testes passaram (`unittest`, Python 3.14, ambiente virtual `.local/venv`). A primeira tentativa falhou por ausência de `prometheus-client`; após instalar `simulator/requirements.txt`, todos passaram. |
| Quatro definições JSON | Parse válido; CPU, Memória, Erro e Sucesso; cada dashboard possui exatamente um painel e referência ao UID `mecaniqa-prometheus`. |
| Scripts PowerShell | Parser não encontrou erros de sintaxe nos scripts versionados. |
| Geração dos ConfigMaps | Executar `sync-grafana-config.ps1` novamente manteve o hash do arquivo gerado. |
| Build das imagens | API Java, MySQL, Redis e simulador construídos pelo script local. |
| Caderno preenchido | DOCX válido como ZIP/XML; três respostas inseridas na seção de 14/10. O documento original foi preservado. |
| Whitespace | `git diff --check` sem erros. |

## Implantação e consultas

| Verificação | Resultado observado |
| --- | --- |
| Cluster | Nó `mecaniqa-control-plane` em `Ready`, Kubernetes 1.34.0. |
| Validação de manifestos | `kubectl apply --dry-run=server -f k8s/` passou; recursos aplicados no contexto `kind-mecaniqa`. |
| Deployments e Pods | API, MySQL, Redis, simulador, Prometheus e Grafana com uma réplica disponível, Pods `1/1 Running`, sem reinícios no registro. |
| Persistência | PVCs de Grafana (1 GiB), Prometheus (5 GiB), MySQL e Redis (1 GiB cada) em `Bound`. |
| Saúde integrada | `http://localhost:18080/health` retornou `status=UP`, `mysql=UP`, `redis=UP`. |
| Grafana | `/api/health` retornou `database=ok`; instância 12.2.0. |
| Fonte de dados | `/api/datasources/uid/mecaniqa-prometheus/health` retornou `status=OK`. |
| Dashboards | API do Grafana retornou exatamente os quatro dashboards com tag `oat2`; cada um possui um painel e a consulta esperada no JSON versionado. |
| Coleta | `up{job="iot-simulator"}=1`. |
| Consultas | As quatro expressões responderam com amostras no Prometheus; valores da conferência abaixo. |
| Exportação | Os quatro dashboards da instância foram exportados pela API para `dashboards-exportados.json`. |
| Interface real | Playwright com Microsoft Edge abriu os quatro dashboards, confirmou a renderização dos gráficos e salvou capturas PNG; comando terminou com saída 0. |

Valores observados na conferência com janela de 1 minuto:

- CPU do processo: aproximadamente **0,0889% de um núcleo**.
- Memória residente: **30.552.064 bytes**, aproximadamente 29,14 MiB.
- Erro da aplicação: **0 leituras rejeitadas/s**.
- Sucesso da aplicação: aproximadamente **1,00007 leituras processadas/s**.

Os valores são uma fotografia da carga sintética normal e mudam durante a execução.
A consulta por API substitui `$__rate_interval` por `1m`; na interface, a janela
é calculada pelo Grafana de acordo com o período e o intervalo de coleta.

O script completo `scripts/deploy-local.ps1` concluiu com sucesso, incluindo a
conferência da API e seus bancos. O script `scripts/validate-monitoring.ps1`
também concluiu com sucesso e salvou as respostas reais em
[validacao-api.json](evidencias/2026-10-14/validacao-api.json).
O inventário está em [recursos-kubernetes.txt](evidencias/2026-10-14/recursos-kubernetes.txt),
e a exportação real em [dashboards-exportados.json](evidencias/2026-10-14/dashboards-exportados.json).

Capturas da interface: [CPU](evidencias/2026-10-14/cpu.png),
[Memória](evidencias/2026-10-14/memoria.png), [Erro](evidencias/2026-10-14/erro.png)
e [Sucesso](evidencias/2026-10-14/sucesso.png).

## Ajustes durante a validação

A importação adicional de Grafana/Prometheus do Docker para o Kind encontrou
`content digest ... not found`, problema de índices multiplataforma descrito nos
[problemas conhecidos do Kind](https://github.com/kubernetes-sigs/kind/blob/main/site/content/docs/user/known-issues.md).
Essas duas imagens foram obtidas pelo runtime do nó com `crictl pull`.
O simulador também foi carregado por arquivo exportado para `linux/amd64`.
As demais imagens do projeto foram carregadas pelo script local, que terminou
normalmente. A configuração global do Docker foi preservada.

Os port-forwards foram reabertos após a prontidão dos Pods. A contagem de dashboards
no verificador foi corrigida para usar o array retornado por `Invoke-RestMethod`
diretamente; depois, os quatro dashboards passaram na conferência.

## Limites

As métricas de CPU e memória medem o processo Python no contêiner Linux, não
todos os serviços ou nós. A coleta estática está configurada para uma réplica.
O sucesso mede processamento sintético local, sem escrita pela API nos bancos.
Alarmes, HPA e teste de estresse pertencem à etapa posterior do caderno.
