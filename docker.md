# Projeto Tinder Gamer - API

Este é o backend do projeto Tinder Gamer, desenvolvido com FastAPI e PostgreSQL.

## Visão Geral da Tecnologia

- **API:** [FastAPI](https://fastapi.tiangolo.com/), um framework web Python moderno e de alta performance.
- **Banco de Dados:** [PostgreSQL](https://www.postgresql.org/), um sistema de banco de dados relacional de código aberto.
- **Containerização:** [Docker](https://www.docker.com/), para criar um ambiente de desenvolvimento consistente e isolado.

## Usando Docker para Desenvolvimento

A configuração do Docker neste projeto automatiza a criação de todo o ambiente de desenvolvimento com apenas alguns comandos. Ele cria dois serviços principais:

1.  `api`: O contêiner que executa a sua aplicação FastAPI.
    -   Ele usa o `Dockerfile` para construir uma imagem Python.
    -   Instala todas as dependências listadas em `requirements.txt`.
    -   Monta o código-fonte local no contêiner, permitindo que as alterações sejam refletidas em tempo real (`hot-reloading`).
    -   Expõe a porta `8000` para que você possa acessar a API a partir do seu navegador.

2.  `db`: O contêiner que executa o banco de dados PostgreSQL.
    -   Usa uma imagem oficial do PostgreSQL.
    -   Persiste os dados do banco de dados em um volume do Docker, para que os dados não sejam perdidos ao parar os contêineres.
    -   Carrega as credenciais do banco de dados a partir do arquivo `.env`.

### Pré-requisitos

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução.

### Como Executar o Ambiente

Siga os passos abaixo no terminal, a partir da pasta `Sistemas-Distribuidos`.

**1. Construa as Imagens dos Contêineres**

Este comando irá construir a imagem para o serviço da `api` conforme definido no `Dockerfile`.

```bash
docker-compose build
```

**2. Inicie os Serviços**

Este comando irá iniciar os contêineres da `api` and `db` em segundo plano (`-d`).

```bash
docker-compose up -d
```

**3. Verifique se Tudo está Rodando**

Para verificar se os contêineres foram iniciados corretamente, execute:

```bash
docker-compose ps
```

Você deve ver dois serviços no estado "Up" ou "Running": `tinder_gamer_api` e `tinder_gamer_db`.

**4. Acesse a API**

Abra seu navegador e acesse a documentação interativa da API:

[http://localhost:8000/docs](http://localhost:8000/docs)

### Comandos Úteis do Docker

-   **Ver os logs da API em tempo real:**
    ```bash
    docker-compose logs -f api
    ```

-   **Ver os logs do banco de dados:**
    ```bash
    docker-compose logs -f db
    ```

-   **Parar todos os serviços:**
    ```bash
    docker-compose down
    ```
    *Use `docker-compose down -v` para parar os serviços e remover os volumes de dados (cuidado: isso apagará seu banco de dados).*
