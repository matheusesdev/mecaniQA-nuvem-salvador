# Runbooks e acordo de continuidade

Segunda entrega de 21/10/2026 da equipe Salvador, baseada na branch de HPA, alarmes e estresse. O [acordo operacional](acordo-operacional.md) define o serviço, as fórmulas e a apuração de SLA, SLO e SLI, as metas de RTO/RPO e a coordenação da resposta. Os quatro runbooks vinculam as regras reais aos comandos do namespace mecaniqa.

| Decisão do caderno | Documento correspondente |
| --- | --- |
| Um runbook por alarme com diagnóstico e recuperação | [CPU](runbooks/cpu.md), [Memória](runbooks/memoria.md), [Erro](runbooks/erro.md), [Sucesso](runbooks/sucesso.md) |
| SLA 99,9% e SLO 99,95% | Acordo operacional com período anual, fórmula e orçamento de indisponibilidade |
| SLI de verificações externas bem-sucedidas | Critério HTTP e dependências, frequência, timeout, lacunas e retenção definidos no acordo |
| RTO 30 min e RPO 15 min | Resposta por tempo decorrido e requisitos para recuperação de dados no acordo |
| Queda de 45 min | Exemplo calculado: viola o RTO, consome 8,56% do orçamento anual de SLA, sem inferir perda de dados |
| Documentação junto às evidências de estresse | [Relatório de validação](validacao-2026-10-21.md) e [arquivos coletados](evidencias/2026-10-21-estresse/) herdados da primeira branch |

Os comandos de diagnóstico foram conferidos no cluster local durante a validação da primeira entrega. As instruções de recuperação descrevem o mesmo encerramento de injeção exercitado pelo script de estresse. Não foi provocado desastre regional nem restauração de banco para validar RTO/RPO; esses números são metas, não resultados medidos.

As URLs de runbook nas regras do Grafana apontam à branch de continuidade no GitHub. Elas só serão acessíveis depois de essa branch ser publicada. Os documentos já podem ser consultados localmente pelos links acima. Após integração, atualizar as URLs para a branch de referência escolhida pela equipe.

A main permanece preservada. Esta branch contém a primeira entrega e a documentação complementar, permitindo revisar o conjunto completo antes de integrar. A apresentação final em PDF e a submissão externa não estão incluídas nestas duas entregas de sessão.
