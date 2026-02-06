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
- MariaDB

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
DB_HOST=seu_host_mariadb
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=nome_do_banco
DB_PORT=3306
DB_TABELA_FOLHAS=nome_da_tabela
```

> **Nota**: Solicite as credenciais ao administrador do sistema.

### 5. Execute a aplicação
```bash
uvicorn backend.main:app --reload
```

> Por padrão, a aplicação será iniciada em http://127.0.0.1:8000. Para personalizar host e porta, use: uvicorn backend.main:app --host 0.0.0.0 --port 8080

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
┌─────────┐      ┌─────────┐      ┌─────────┐      ┌──────────┐
│Frontend │─────>│ FastAPI │─────>│ MariaDB │      │Arquivo   │
│(HTML/JS)│      │(Backend)│      │         │      │PDF (rede)│
└─────────┘      └─────────┘      └─────────┘      └──────────┘
     ▲                │                 │                 │
     │                └─────────────────┴─────────────────┘
     │                          (Backend busca PDF)
     └────────────────────────────────────────────────────┘
                         (Serve PDF)
```

1. Usuário insere OF
2. Backend consulta caminho do PDF no MariaDB
3. Backend localiza e lê o arquivo PDF na rede
4. PDF é servido para visualização no navegador

### Banco de Dados

**Tabela de Processos**:

| Campo     | Tipo    | Descrição                    |
|-----------|---------|------------------------------|
| `of`      | INT     | Ordem de Fabricação (chave)  |
| `caminho` | VARCHAR | Caminho do PDF na rede       |

**Conexão**: PyMySQL + MariaDB (configurado via `.env`)

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.