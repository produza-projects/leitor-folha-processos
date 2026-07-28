# Leitor de Folha de Processos

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/Python-3.12.10-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?logo=bootstrap&logoColor=white)


Aplicação web interna para consulta e visualização de folhas de processos em PDF através de OF (Ordem de Fabricação), via digitação manual ou leitura de QR Code.

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação](#instalação)
- [Migrations do Banco](#migrations-do-banco)
- [Como Usar](#como-usar)
- [Estrutura Técnica](#estrutura-técnica)
- [Licença](#licença)

## Sobre o Projeto

O **Leitor de Folha de Processos** facilita o acesso rápido a documentos de processos produtivos através da consulta por OF (Ordem de Fabricação).

### Benefícios

- **Acesso instantâneo**: Localização de documentos sem busca manual no sistema de arquivos
- **Visualização simultânea**: Permite que múltiplos usuários consultem o mesmo documento sem bloqueio de edição
- **Interface simplificada**: Reduz tempo de consulta com design intuitivo

## Funcionalidades

- Consulta por digitação manual da OF
- Leitura de QR Code para acesso instantâneo
- Visualização de PDF diretamente no navegador
- Interface responsiva

## Tecnologias Utilizadas

### Backend
- **Python 3.12.10**
- **FastAPI 0.110.0**

### Frontend
- **HTML5**
- **JavaScript**
- **CSS3**
- **Bootstrap 5.3.3**

### Banco de dados
- PostgreSQL

### Outras Dependências
- Bibliotecas Python (conforme `requirements.txt`)

## Instalação

Siga os passos abaixo para configurar o projeto localmente:

### 1. Clone o repositório e acesse-o

```bash
git clone https://github.com/produza-projects/leitor-folha-processos.git
cd leitor-folha-processos
```

### 2. Configure o ambiente virtual

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as credenciais do banco de dados:
```env
POSTGRES_HOST=seu_host_postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=nome_do_banco
POSTGRES_USERNAME=seu_usuario
POSTGRES_PASSWORD=sua_senha
```

> **Nota**: Solicite as credenciais ao administrador do sistema.

### 5. Execute a aplicação
```bash
uvicorn backend.main:app --reload
```

> Por padrão, a aplicação será iniciada em http://127.0.0.1:8000. Para personalizar host e porta, use: uvicorn backend.main:app --host 0.0.0.0 --port 8080

## Migrations do Banco

Este repositório é a fonte oficial do schema compartilhado do banco
`gerenciador_fp`. Tabelas, índices, constraints e futuras alterações ficam em
`database/migrations/` e não devem ser duplicados em scripts de infraestrutura
ou no repositório de sincronização.

O repositório `server-infra` cria o database PostgreSQL, provisiona as
credenciais e orquestra `migrate up` antes de iniciar as aplicações. A imagem
Docker deste projeto inclui o CLI `migrate` e copia as migrations para:

```text
/app/database/migrations
```

Para aplicar localmente, instale o CLI
[`golang-migrate`](https://github.com/golang-migrate/migrate) e execute:

```bash
export DATABASE_URL='postgres://usuario:senha@localhost:5432/gerenciador_fp?sslmode=disable'
make migrate-up
make migrate-version
```

Uma migration já aplicada é imutável. Mudanças futuras devem ser adicionadas em
novos pares `.up.sql` e `.down.sql`; não edite `000001_initial_schema` depois de
ela ter sido usada em qualquer ambiente compartilhado.

Ao criar tabelas ou sequences, a mesma migration deve incluir os grants mínimos
para os usuários consumidores, condicionados à existência das roles. Não use
`ALTER DEFAULT PRIVILEGES`, pois ele também poderia expor a tabela interna
`schema_migrations`.

O arquivo de criação do database não pertence a este repositório. Em ambientes
gerenciados, essa responsabilidade é do `server-infra`.

Nos Composes locais, a aplicação usa as redes externas lógicas `proxy` e
`database`, com nomes `server-infra-<ambiente>_proxy` e
`server-infra-<ambiente>_database`. O hostname PostgreSQL dentro da rede é
`postgres`; não use IP de container nem publique a porta do banco.


## Publicação com HTTPS via nginx

A aplicação pode continuar escutando HTTP internamente na rede Docker, em `leitor-folha-processos:8000`. O HTTPS deve ser terminado no container nginx que está na mesma rede externa `proxy`.

Exemplo de vhost nginx: [`nginx/leitor-folha-processos.https.conf.example`](nginx/leitor-folha-processos.https.conf.example).

Checklist de implantação:

1. Garanta que o container nginx também esteja conectado à rede Docker externa `proxy`.
2. Configure o vhost com `server_name fp.abc.local`.
3. Instale no nginx um certificado válido para `fp.abc.local`.
4. Exponha/publice as portas `80` e `443` no container nginx.
5. Peça para a TI apontar o DNS `fp.abc.local` para o IP do servidor onde o nginx atende.
6. Recarregue o nginx após instalar o arquivo de configuração e os certificados.

Para ambiente interno, o certificado normalmente deve ser emitido pela CA interna da empresa. Um certificado self-signed também funciona tecnicamente, mas cada estação cliente precisará confiar na CA/certificado para o navegador não exibir alerta de segurança.

## Como Usar

### Digitação Manual

1. Digite a OF no campo de entrada
2. Pressione Enter ou clique em "Buscar"
3. O PDF será exibido se existir

### QR Code

1. Clique no botão de leitura de QR Code
2. Escaneie o código
3. O PDF será carregado automaticamente

## Estrutura Técnica

### Arquitetura

**Fluxo de requisição**:
```
┌─────────┐      ┌─────────┐      ┌──────────┐     ┌──────────┐
│Frontend │─────>│ FastAPI │─────>│PostgreSQL│     │Arquivo   │
│(HTML/JS)│      │(Backend)│      │          │     │PDF (rede)│
└─────────┘      └─────────┘      └──────────┘     └──────────┘
     ▲                │                 │                 │
     │                └─────────────────┴─────────────────┘
     │                          (Backend busca PDF)
     └────────────────────────────────────────────────────┘
                         (Serve PDF)
```

1. Usuário insere OF
2. Backend consulta caminho do PDF no PostgreSQL
3. Backend localiza e lê o arquivo PDF na rede
4. PDF é servido para visualização no navegador

### Banco de Dados

**Tabelas de Processos**:

| Tabela                | Campo                | Descrição                   |
|-----------------------|----------------------|-----------------------------|
| `caminhos`            | `id`                 | Identificador do caminho    |
| `caminhos`            | `cod_produto`        | Código do produto           |
| `caminhos`            | `caminho`            | Caminho do PDF na rede      |
| `ordens_fabricacao`   | `ordem_fabricacao`   | Ordem de fabricação         |
| `ordens_fabricacao`   | `caminho_id`         | Referência para `caminhos`  |

**Conexão**: psycopg2 + PostgreSQL (configurado via `.env`)

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
