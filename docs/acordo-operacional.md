# Acordo operacional de continuidade da MecaniQA

A equipe Salvador adota este acordo para orientar a resposta aos quatro alarmes e a avaliação da continuidade do serviço. O documento atende à segunda sessão de 21/10/2026 e acompanha a implementação e as evidências da primeira sessão. As metas abaixo são compromissos de projeto acadêmico, sem demonstração de disponibilidade anual em produção.

## Serviço e medição

O serviço observado pelo cliente é a API Java e sua dependência de MySQL e Redis. O simulador IoT é uma demonstração separada: seus contadores de sucesso e erro não medem a disponibilidade da API nem provam persistência das leituras. CPU e RSS ajudam a operar o simulador, mas não substituem o SLI externo.

| Conceito | Definição e meta adotada |
| --- | --- |
| SLA | Acordo com o cliente Enterprise: disponibilidade mínima de 99,9% por ano civil. Todas as falhas observadas contam, inclusive manutenção; não há exclusões previstas neste exercício. |
| SLO | Objetivo interno mais exigente: disponibilidade de 99,95% no mesmo período. A diferença de 0,05 ponto percentual é a margem para agir antes de descumprir o SLA. |
| SLI | 100 × verificações externas bem-sucedidas / verificações externas previstas. Uma verificação a cada 60 segundos ao endereço externo da API, GET /health, timeout de 5 segundos; sucesso exige HTTP 200, status UP, mysql UP e redis UP. Falta de registro conta conservadoramente como falha até investigação e deve ser identificada como lacuna do monitor. |
| RTO | Máximo de 30 minutos entre o início da interrupção e o restabelecimento validado da API e das dependências. O tempo de detecção integra esse orçamento. |
| RPO | Máximo de 15 minutos de dados transacionais perdidos, medidos entre a última transação durável recuperável e o instante da interrupção. Não equivale ao período de scrape do Prometheus nem à frequência de verificações externas. |

A sonda deve executar fora do cluster e da região monitorada, registrar timestamp UTC, resultado, tempo de resposta e destino, e manter os registros por pelo menos o ano de apuração. No laboratório, localhost:18080/health só demonstra o acesso pelo host; não constitui medição externa independente da região. As requisições da sonda não devem registrar senhas ou payloads de clientes.

Para cada minuto previsto, há no máximo uma amostra contabilizada. Sem amostras previstas no período, o SLI é indefinido, não 100%. O resultado anual compara a proporção com o SLA e o SLO; médias de percentuais mensais não devem substituir a contagem ponderada. O orçamento disponível é o total do período multiplicado pela fração tolerada de falhas.

## Orçamento de indisponibilidade

Para um ano de 365 dias, existem 525.600 minutos. O SLA admite até 525,6 minutos de indisponibilidade, ou 8h45min36s; o SLO admite até 262,8 minutos, ou 4h22min48s. Em ano bissexto, os valores passam a 527,04 e 263,52 minutos. A apuração por sondas de um minuto tem essa resolução e deve divulgar a incerteza nos limites do incidente.

Uma queda regional de 45 minutos ultrapassa o RTO de 30 minutos em 15 minutos. Isoladamente, utiliza aproximadamente 8,56% do orçamento anual de SLA e resulta em disponibilidade de cerca de 99,99144% em ano de 365 dias, se não houver outras falhas. Não viola sozinha o SLA de 99,9%, mas precisa ser somada às demais interrupções. A duração da queda não informa a perda de dados: é necessário comparar os dados recuperados com o RPO.

## Resposta e responsabilidades

O QA Rafael Pires Araújo acompanha as verificações, registra o horário do incidente e valida o encerramento. O piloto Juan Pablo Barros Carvalho conduz o diagnóstico; o copiloto Matheus Espírito Santo dos Santos executa e confere as ações. O Scrum Master Albert Santos Soares coordena prioridades e o registro de comunicação. O caderno não indica um arquiteto para estas sessões. Esses papéis organizam o exercício e não estabelecem uma escala real de atendimento permanente.

1. Até 5 minutos: reconhecer o incidente, confirmar o impacto externo e abrir o registro com timestamps, alarme, réplicas e alterações recentes.
2. Até 10 minutos: consultar o runbook correspondente, comparar CPU, RSS, erros, sucesso e saúde das dependências. Escalonar ao piloto e ao coordenador se não houver causa identificada.
3. Até 20 minutos: executar a recuperação adequada, verificar a API externamente e preparar alternativa se a recuperação local não avançar. Não apagar PVCs para tentar resolver uma falha.
4. Até 30 minutos: concluir a recuperação e validar os dados. Se o serviço continuar indisponível, registrar a violação de RTO e atualizar o responsável pela comunicação; não redefinir o início da contagem.

## Recuperação e proteção dos dados

Volumes persistentes protegem contra substituição de Pods, mas não garantem RPO em perda de nó, disco ou região. Para atingir RPO de 15 minutos em um ambiente real, o MySQL precisaria de backup consistente e logs transacionais recuperáveis fora da região, com ponto recuperável no máximo 15 minutos anterior à falha. O Redis deve ter sua função definida: se for cache reconstruível, restaurar a fonte durável; se guardar dados únicos, também requer política de persistência e cópia externa. As leituras sintéticas atuais não são gravadas em nenhum deles.

A recuperação regional exige provisionar cluster e rede alternativos, restaurar secrets por canal protegido, aplicar a versão aprovada dos manifestos e imagens, restaurar MySQL ao ponto recuperável, verificar consistência e reconstruir o Redis quando aplicável. Só redirecionar tráfego depois de validar /health e operações de negócio. Medir o tempo completo, confirmar o último dado recuperado e comparar com RTO/RPO.

Backup externo, recuperação pontual, ambiente em outra região, DNS de failover e monitor externo contínuo não estão implementados neste laboratório. O teste local de HPA e alarmes não valida desastre regional nem demonstra cumprimento do RPO. Esses controles são pré-requisitos para assumir as metas em produção.

## Runbooks e encerramento

Cada alarme possui condição de disparo, impacto, comandos de diagnóstico, recuperação e critérios de encerramento:

- [CPU](runbooks/cpu.md)
- [Memória](runbooks/memoria.md)
- [Erro na aplicação](runbooks/erro.md)
- [Sucesso na aplicação](runbooks/sucesso.md)

Encerrar um incidente quando os quatro alarmes estiverem normais, a coleta estiver saudável, não houver reinícios crescentes, o HPA estiver estável e a API estiver UP com os bancos. Confirmar pelo menos cinco verificações externas consecutivas, registrar o intervalo real da interrupção, perda de dados medida, RTO observado, impacto no orçamento e responsável pela revisão. No laboratório, a estabilização do HPA pode acrescentar mais de cinco minutos após retirar a carga; isso é comportamento esperado e deve ser acompanhado.

## Evidências e revisão

A evidência da sessão anterior está em [evidências de estresse](evidencias/2026-10-21-estresse/). Timestamps representam a execução efetiva, não a data nominal da aula. Amostras, logs e capturas devem ser analisados em conjunto. A aprovação do teste local comprova quatro alarmes e autoscaling naquele cenário sintético, sem afirmar capacidade para milhares de sensores reais.

O acordo deve ser revisto ao mudar limites, requests, regras, fonte dos dados ou responsabilidades. O professor avalia o conteúdo integrado à main e a apresentação final no modelo indicado; as duas branches permitem revisão antes dessa integração.
