# Respostas ao caderno de guias — OAT 1

Respostas baseadas nos arquivos atuais do projeto para os encontros de 26/08,
02/09 e 09/09/2026. Os campos abaixo correspondem a “Decisão da Equipe”.

## 26/08/2026 — A Anatomia da Imagem

Utilizamos `eclipse-temurin:17-jdk-alpine`, que fornece o JDK 17 sobre Alpine
Linux para compilar e executar a aplicação Java. O contêiner compartilha o kernel
do ambiente hospedeiro, sem executar um sistema operacional completo para cada
serviço, tornando essa abordagem mais leve que uma máquina virtual tradicional.

## 26/08/2026 — Isolamento e Exposição

Declaramos `EXPOSE 8080` no Dockerfile da API e publicamos a porta com
`-p 8080:8080` no Docker run ou `8080:8080` no Compose.
`ENTRYPOINT ["java", "-jar", "app.jar"]` executa a aplicação como processo principal
e mantém o contêiner ativo enquanto esse processo estiver em execução.

## 02/09/2026 — A Comunicação Interna (DNS)

Conectamos os serviços à rede `mecaniqa_network` e configuramos a API com
`DB_HOST=db` e `REDIS_HOST=redis`. O DNS interno do Docker resolve os nomes dos
serviços sem IPs fixos. A API aguarda os health checks dos bancos antes de iniciar
e utiliza `/health` para verificar a conectividade TCP com ambos.

## 02/09/2026 — A Persistência de Dados

O volume `mysql_data`, montado em `/var/lib/mysql`, mantém os dados do MySQL
quando o contêiner reinicia ou é recriado, desde que o volume seja preservado
e reutilizado. O Redis utiliza `redis_data` em `/data` com AOF habilitado.
Os dados armazenados pelos bancos ficam separados do ciclo de vida dos contêineres.

## 09/09/2026 — Unidade Básica e Estado Desejado

Um Pod isolado não possui um controlador responsável por substituí-lo se for
removido. O Deployment da API declara uma réplica e mantém esse estado desejado:
se o Pod for perdido ou excluído, cria outro. As probes verificam a inicialização,
a disponibilidade e a prontidão da aplicação.

## 09/09/2026 — Estratégia de Exposição (Services)

MySQL e Redis utilizam Services `ClusterIP` para acesso interno pela API, pelos
nomes `mysql` e `redis`. A API utiliza `NodePort` na porta `30080`, encaminhada
para sua porta `8080`, permitindo acesso externo. No Kind local, esse acesso
é mapeado para `localhost:18080`.

## Informações que dependem de confirmação da equipe

- Confirmar os integrantes e os papéis em cada encontro. O caderno enviado
  contém campos vazios e o nome Lucas Almeida Silva no primeiro encontro,
  divergindo dos registros de equipe do README.
- Confirmar o convite ao professor no repositório.
- Registrar as evidências de builds e testes isolados dos três serviços.
- Repetir a validação no ambiente disponível e registrar métricas no K9s.

O caderno original não foi alterado. As respostas estão prontas para transcrição;
os nomes e papéis não foram inferidos.
