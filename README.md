# Leitor de Folha de Processos

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688?logo=fastapi&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?logo=bootstrap&logoColor=white)


Aplicação web interna para consulta e visualização de folhas de processos em PDF
por Ordem de Fabricação (OF), número serial ou código do produto.

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação](#instalação)
- [Migrations do Banco](#migrations-do-banco)
- [Autenticação com Keycloak](#autenticação-com-keycloak)
- [Publicação das Imagens](#publicação-das-imagens)
- [Publicação com HTTPS via Traefik](#publicação-com-https-via-traefik)
- [Como Usar](#como-usar)
- [Estrutura Técnica](#estrutura-técnica)
- [Testes](#testes)
- [Licença](#licença)

## Sobre o Projeto

O **Leitor de Folha de Processos** facilita o acesso rápido a documentos de
processos produtivos por OF, número serial ou código do produto.

### Benefícios

- **Acesso instantâneo**: Localização de documentos sem busca manual no sistema de arquivos
- **Visualização simultânea**: Permite que múltiplos usuários consultem o mesmo documento sem bloqueio de edição
- **Interface simplificada**: Reduz tempo de consulta com design intuitivo

## Funcionalidades

- Consulta por OF de 7 dígitos
- Consulta por número serial, utilizando os 7 primeiros dígitos como OF
- Consulta por código do produto no formato `0000.000000`
- Visualização de PDF diretamente no navegador
- Interface responsiva
- Login centralizado pelo Keycloak em ambientes gerenciados
- Autorização pela role de client `viewer`

## Tecnologias Utilizadas

### Backend
- **Python 3.12**
- **FastAPI 0.141.1**

### Frontend
- **HTML5**
- **JavaScript**
- **CSS3**
- **Bootstrap 5.3.3**

### Banco de dados
- PostgreSQL

### Outras Dependências
- Bibliotecas Python (conforme `requirements.txt`)

### Compartilhamento de PDFs

Em ambientes gerenciados, o servidor deve montar o compartilhamento SMB/CIFS em
`/mnt/boro_documentacao_geral` antes de iniciar a aplicação. O Compose fornece
esse diretório ao container como bind mount somente leitura e não cria a origem
automaticamente quando ela estiver ausente.

Usuário e senha do compartilhamento pertencem à infraestrutura do servidor;
eles não devem ser adicionados ao `.env`, ao banco de dados ou à imagem.

Os arquivos em `docker/` também servem ao uso local e não implementam a
dependência de boot do servidor. No host gerenciado, inicie a aplicação somente
pela unit systemd gerada pelo `server-infra`; ela valida o CIFS antes de permitir
que o container suba.

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

Crie um arquivo `.env` na raiz do projeto, tomando `.env.example` como base, e
configure as credenciais do banco de dados:

```env
POSTGRES_HOST=seu_host_postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=nome_do_banco
POSTGRES_USERNAME=seu_usuario
POSTGRES_PASSWORD=sua_senha
OIDC_ENABLED=false
```

> **Nota**: Solicite as credenciais ao administrador do sistema. Para execução
> local sem Keycloak, mantenha `OIDC_ENABLED=false`. As demais variáveis OIDC
> estão documentadas em `.env.example` e são obrigatórias quando a autenticação
> estiver habilitada.

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

A migration `000002_normalize_product_codes` remove espaços laterais dos códigos
existentes depois de validar que não há formatos inválidos ou duplicidades
lógicas. Em seguida, uma constraint garante que `caminhos.cod_produto` permaneça
exatamente no formato `0000.000000`. Implante primeiro uma versão do
`leitor-folha-processos-data-sync` que normalize os valores recebidos do
Protheus; caso contrário, novas sincronizações serão corretamente rejeitadas
pela constraint.

Ao criar tabelas ou sequences, a mesma migration deve incluir os grants mínimos
para os usuários consumidores, condicionados à existência das roles. Não use
`ALTER DEFAULT PRIVILEGES`, pois ele também poderia expor a tabela interna
`schema_migrations`.

O arquivo de criação do database não pertence a este repositório. Em ambientes
gerenciados, essa responsabilidade é do `server-infra`.

Nos Composes locais, a aplicação usa as redes externas lógicas `proxy` e
`auth` e `database`, com nomes `server-infra-<ambiente>_proxy`,
`server-infra-<ambiente>_auth` e
`server-infra-<ambiente>_database`. O hostname PostgreSQL dentro da rede é
`postgres`; não use IP de container nem publique a porta do banco.

## Autenticação com Keycloak

Em `dev`, a aplicação é um client confidencial OIDC chamado
`leitor-folha-processos` no realm `produza-dev`. O fluxo usado é Authorization
Code com PKCE S256. O backend troca e valida os tokens; o navegador recebe
somente o cookie de sessão assinado `fp_session`, com `HttpOnly`, `Secure` e
`SameSite=Lax`. Tokens e client secret não são gravados no JavaScript nem no
`localStorage`.

As rotas `/`, `/api/me` e `/buscar/{serial}` exigem login, e a consulta de PDF
exige a client role `viewer`. `/healthz` permanece público para healthchecks. A
sessão local dura uma hora e um novo login é solicitado ao expirar.

O backend usa duas URLs para o mesmo realm:

- `OIDC_PUBLIC_ISSUER`: URL HTTPS vista pelo navegador e declarada no token;
- `OIDC_INTERNAL_ISSUER`: URL HTTP privada `http://keycloak:8080` usada somente
  entre containers na rede `auth` para token e chaves públicas.

Em ambiente gerenciado, os valores ficam em
`/opt/<ambiente>/secrets/leitor-folha-processos.env`. O
`OIDC_CLIENT_SECRET` deve ser exatamente o secret da aba Credentials do client
no Keycloak. `OIDC_SESSION_SECRET` é independente e pode ser gerado com:

```bash
openssl rand -hex 32
```

Não envie nenhum dos dois ao Git nem os reutilize em outro ambiente. Para
execução local sem Keycloak, use `OIDC_ENABLED=false`, conforme `.env.example`.

O login corporativo é federado pelo Keycloak ao Google por OIDC. A aplicação
não recebe o Client ID, o Client Secret nem tokens do Google e não valida
domínios diretamente. O Keycloak aceita o claim corporativo `hd` somente para
`produza.ind.br` e `certi.org.br` e adiciona esses usuários ao grupo que concede
a client role `viewer`.

O OIDC básico do Google não sincroniza grupos do Workspace. A política atual é
permitir todos os usuários dos dois domínios. Uma conta local do Keycloak,
inclusive com e-mail `@gmail.com`, continua podendo autenticar por senha, mas só
acessa esta aplicação quando um administrador lhe atribui explicitamente a
client role `viewer` ou o grupo correspondente. O domínio do e-mail de uma conta
local não concede permissão.

## Publicação das Imagens

O workflow `.github/workflows/publish-dev-image.yml` é executado em todo push
para a branch `dev`. Ele constrói a imagem, inicia um container temporário,
valida o endpoint `/healthz` e somente então publica a imagem no GHCR com uma
tag imutável no formato:

```text
ghcr.io/produza-projects/leitor-folha-processos:dev-<commit-curto>
```

O workflow `.github/workflows/publish-production-image.yml` aplica as mesmas
validações aos pull requests destinados à `main`. Após o merge, o push na
`main` publica a imagem de produção no formato:

```text
ghcr.io/produza-projects/leitor-folha-processos:prod-<commit-curto>
```

Nenhum dos fluxos publica a tag mutável `latest`. A promoção para produção é
feita pelo merge controlado de `dev` em `main`; o deploy usa sempre o digest
SHA-256 gerado pelo workflow da `main`.

A autenticação usa o `GITHUB_TOKEN` fornecido pelo próprio GitHub Actions, com
acesso somente de leitura ao conteúdo do repositório e escrita em packages.
Nenhum token adicional deve ser criado ou salvo como secret do projeto.

O resumo da execução registra a tag e o digest da imagem publicada. Use o
digest informado ao executar o playbook de deploy do `server-infra`.

O package no GHCR deve permanecer acessível ao servidor conforme a política do
repositório. Quando ele for privado, o servidor precisa usar uma credencial com
permissão mínima `read:packages`.


## Publicação com HTTPS via Traefik

A aplicação escuta HTTP somente dentro da rede Docker, em
`leitor-folha-processos:8000`. O Traefik compartilhado é o único container que
publica uma porta no host e encaminha as requisições pela rede `proxy` isolada
de cada ambiente.

O HTTPS externo é finalizado pela infraestrutura gerenciada pela TI, que
encaminha HTTP para a porta 80 do Traefik no servidor. O deploy oficial,
incluindo hostnames, labels e ciclo de vida do proxy, pertence ao repositório
`server-infra`.

| Ambiente | Hostname | Rede do proxy |
| --- | --- | --- |
| Desenvolvimento | `fp-dev.produza.ind.br` | `server-infra-dev_proxy` |
| Produção | `fp.produza.ind.br` | `server-infra-prod_proxy` |

Para um diagnóstico que não dependa do DNS, use:

```bash
curl --noproxy '*' \
  --resolve fp-dev.produza.ind.br:80:172.16.8.246 \
  http://fp-dev.produza.ind.br/healthz
```

Esse comando valida diretamente a origem HTTP e não representa o acesso normal
dos usuários, que ocorre por HTTPS. A porta `8000` permanece sem publicação no
host.

Para diagnóstico local excepcional, publique apenas em loopback usando o
override dedicado:

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.dev.yml \
  -f docker/compose.diagnostics.yml \
  up
```

## Como Usar

### Valores aceitos

- **OF:** exatamente 7 dígitos, por exemplo `2619006`.
- **Número serial:** os 7 primeiros dígitos devem representar a OF. Qualquer
  sequencial posterior é desconsiderado na consulta.
- **Código do produto:** exatamente 4 dígitos, um ponto e mais 6 dígitos, por
  exemplo `5000.001622` ou `5001.009867`.

O valor completo é primeiro comparado com o formato de código do produto
`^\d{4}\.\d{6}$`. Quando houver correspondência, a consulta utiliza o código
integral e igualdade exata em `caminhos.cod_produto`. Caso contrário, a
aplicação mantém o comportamento de OF/serial e utiliza os 7 primeiros
caracteres.

### Consulta

1. Digite a OF, o número serial ou o código do produto no campo de entrada.
2. Pressione Enter ou clique em **Buscar**.
3. Quando encontrado, o PDF é aberto em uma nova aba do navegador.
4. Quando não houver registro ou arquivo, a interface exibe a mensagem de erro
   correspondente.

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

1. O usuário insere uma OF, um número serial ou um código do produto.
2. A aplicação identifica códigos de produto antes de aplicar o corte de 7
   caracteres usado por OF e serial.
3. O backend consulta o PostgreSQL por igualdade exata em
   `caminhos.cod_produto` ou pela OF em `ordens_fabricacao`.
4. O backend obtém o caminho armazenado em `caminhos.caminho`.
5. O arquivo é localizado no compartilhamento de rede e servido como PDF para
   visualização no navegador.

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

## Testes

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Execute a suíte completa sem criar cache ou bytecode no diretório do projeto:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

Para reproduzir também a auditoria de dependências executada pelo CI:

```bash
pip-audit --requirement requirements.txt
```

Os workflows de desenvolvimento e produção executam os testes e a auditoria
antes da construção e publicação das imagens.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
