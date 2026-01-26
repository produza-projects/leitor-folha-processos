# Leitor de Folha de Processos

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/Python-3.12.10-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?logo=bootstrap&logoColor=white)


Aplicação web interna para leitura de serial number, via digitação manual ou QR Code, e visualização da folha de processos em PDF diretamente no navegador.

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Licença](#licença)

## Sobre o Projeto

O **Leitor de Folha de Processos** é uma solução web desenvolvida para facilitar o acesso rápido e eficiente a documentos de processos através da leitura de serial numbers. A aplicação permite que os usuários localizem e visualizem folhas de processos em formato PDF de forma intuitiva e prática.

### Problema Resolvido

- Elimina a necessidade de busca manual em arquivos no sistema, permitindo acesso instantâneo aos documentos através da leitura de códigos. 
- Elimina a bloqueio à edição dos arquivos caso estejam abertos em outros máquinas.

## Funcionalidades

- **Digitação Manual**: Insira o serial number manualmente para buscar o documento
- **Leitura de QR Code**: Escaneie QR Codes para acesso instantâneo
- **Visualização em PDF**: Exiba os documentos diretamente no navegador
- **Interface Intuitiva**: Design simples e responsivo para facilitar o uso
- **Acesso Rápido**: Localização instantânea de documentos

## Tecnologias Utilizadas

### Backend
- **Python 3.12.10**
- **FastAPI 0.110.0**

### Frontend
- **HTML5**
- **JavaScript**
- **CSS3**
- **Bootstrap 5.3.3**

### Outras Dependências
- Bibliotecas Python (conforme `requirements.txt`)

## Instalação

Siga os passos abaixo para configurar o projeto localmente:

### 1. Clone o repositório e acesse-o

```bash
git clone https://github.com/produza-projects/leitor-folha-processos.git
cd leitor-folha-processos
```

### 2. Crie um ambiente virtual

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

```env
CAMINHO_DATABASE_FP=
```

### 5. Execute a aplicação

```bash
uvicorn backend.main:app --reload
```

## Como Usar

### Método 1: Digitação Manual

1. Acesse a aplicação no navegador
2. Digite o serial number no campo de entrada
3. Clique em "Buscar" ou pressione Enter
4. O PDF será exibido automaticamente, caso exista

### Método 2: QR Code

1. Acesse a aplicação no navegador
2. Faça a leitura do QR Code
3. O PDF será carregado automaticamente, caso exista

## Estrutura do Projeto

```
leitor-folha-processos/
├── backend/                # Código do servidor backend
│   ├── main.py               # Arquivo principal da aplicação
├── frontend/               # Arquivos do frontend
│   ├── index.html            # Página principal
│   ├── js/                   # Scripts JavaScript
├── .gitignore              # Arquivos ignorados pelo Git
├── LICENSE                 # Licença MIT
├── requirements.txt        # Dependências Python
└── README.md               # Este arquivo
```

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.