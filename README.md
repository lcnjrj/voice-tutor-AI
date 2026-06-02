# voice-tutor-AI: AI-Powered Language Assistant

O **Voice Tutor** é um assistente inteligente tipo dicionario em tempo real projetado para o aprendizado e prática de novos idiomas. O projeto nasceu originalmente como um desafio prático de infraestrutura de dados na nuvem da **DIO (Digital Innovation One)** e foi expandido para se tornar uma aplicação *full-stack* para outro curso na Dio.

A aplicação permite que o usuário interaja por voz através de uma interface web dinâmica, processa o contexto pedagógico com IA avançada, sintetiza respostas com vozes neurais nativas sem sotaque e persiste de forma limpa todo o histórico de interações em nuvem.

Usei o gemini para conseguir melhorar a voz de saíde pedido que ele criasse uma forma do sistema Edge-TTS nãolesse a pontuação.

---

## 🛠️ Arquitetura do Sistema

O projeto foi desenhado focando em modularidade, alta qualidade de áudio e **eficiência econômica extrema**:

* **Front-end:** Interface interativa construída em Python usando **Gradio**, simplificando a captura de áudio direto do microfone.
* **Cérebro da IA:** **Google Gemini 2.5 Flash**, gerenciando o contexto histórico da conversa e atuando como um tutor pedagógico.
* **Síntese de Voz (TTS):** **Edge-TTS** (Microsoft Neural Voices) integrado à biblioteca **Pydub**, permitindo fatiamento e costura de áudio para alternância dinâmica de idiomas.
* **Camada de Persistência:** **Azure SQL Database** configurado em nível de computação **Serverless**, garantindo persistência relacional de nível corporativo.

---
O **Gradio** é uma biblioteca do Python que cria interfaces gráficas interativas e **páginas web** para modelos de inteligência artificial em poucos minutos.
Ele gera automaticamente componentes de entrada e saída (como gravadores de áudio e caixas de texto) e fornece links públicos para testar o app em qualquer dispositivo.
Você pode personalizar de três formas: temas Prontos, CSS Customizado e estrutura de Blocos (Blocks). 



---
## 💸  Custo-Beneficio do Serverless

Embora um banco de dados relacional não fosse estritamente obrigatório para o app, a escolha do **Azure SQL Serverless** foi feita para simular um ambiente de produção real com custo praticamente zero para o desenvolvedor:

1. **Computação sob Demanda:** A cobrança por processamento (vCores) ocorre apenas nos segundos exatos em que a aplicação realiza operações de escrita (`INSERT`) ou leitura (`SELECT`).
2. **Recurso de Pausa Automática (Auto-Pause):** O banco de dados foi configurado com uma regra de inatividade de 1 hora. Quando o Voice Tutor não está sendo usado, a Azure suspende a computação automaticamente, reduzindo o custo de processamento para **zero** e cobrando apenas centavos pelo armazenamento físico dos dados. 

Aqui está um mini explicativo direto e visual de como os dados saem do seu arquivo **app.py** e chegam ao **Azure SQL**, ideal para fixar o conceito ou usar como resumo.

---

## `app.py` ➔ Azure SQL

Quando você fala no microfone, o dado faz exatamente este caminho:

```
[ Usuário Fala ] ➔ [ Gradio ] ➔ [ Gemini AI ] ➔ [ app.py (Variaveis) ]
                                                        │
                                                        ▼
[ Azure SQL (Nuvem) ] ◀─── [ Driver ODBC 18 ] ◀─── [ pyodbc ]

```

### 1. A Captura e a Ponte (`pyodbc`)

Dentro do `app.py`, as variáveis `texto_usuario` e `resposta_ia` guardam os textos puros da conversa. Quando a função `salvar_interacao` é chamada, a biblioteca **pyodbc** entra e funciona como um tradutor que pega essas variáveis do Python e as prepara para o formato do banco de dados.

### 2. A Estrada (`Driver ODBC 18` + `Firewall`)

O **Driver ODBC 18** (que instalei no no pc Linux) abre um caminho de comunicação criptografado e seguro com a internet. Esse caminho leva até os servidores da Microsoft Azure, cruza a barreira do **Firewall** (onde meu IP local foi previamente autorizado) e bate na porta `1433` do seu servidor lógico.

### 3. A Persistência (`INSERT`)

O comando SQL é disparado:

```sql
INSERT INTO HistoricoConversas (texto_usuario, resposta_ia) VALUES (?, ?)

```

O Azure SQL recebe a instrução, processa na camada **Serverless** (ligando os motores de vCore se o banco estava pausado), grava os textos definitivamente nos discos rígidos da nuvem e devolve um sinal de sucesso para o terminal do seu Linux.

---


* **Dados Eternos:** Mesmo se você desligar o computador ou resetar o Linux, o seu progresso de estudos está salvo em um datacenter seguro da Microsoft.
* **Economia Dinâmica:** O `app.py` faz a gravação em milissegundos e o banco já se prepara para pausar de novo, garantindo que você tenha um ecossistema profissional gastando quase nada.


3.**Custos**

Criei regras de uso para manter o consumo da API Gemini dentro dolimite  gratuito.

No Azure, se atingir o limite de dados para o serviço automaticamente e só reinicia noproximo mês,assim mantendo custo zero

4. **Processamento de Áudio Gratuito:** Para evitar o custo volumoso de APIs de voz baseadas em consumo por caractere (como OpenAI TTS), o processamento de voz neural multilíngue é delegado ao `edge-tts` com o ecossistema local do `ffmpeg`, eliminando custos operacionais de áudio.

---

## ✨ Recursos de Destaque

* **Alternância Dinâmica de Vozes (Code-Switching):** O sistema quebra a resposta da IA e alterna o motor de voz em tempo real (ex: usando a voz `FranciscaNeural` para explicações em português e mudando instantaneamente para a voz `JennyNeural` ao pronunciar termos nativos em inglês).
* **Normalização de Dados via Regex:** Filtros avançados com Expressões Regulares (`re.sub`) limpam caracteres Markdown (asteriscos, hashtags) enviados pela IA, impedindo ruídos ou leituras literais indesejadas pelo sintetizador de voz.
* **Dual-Text Pipeline:** Separação estrita entre o texto fonético adaptado enviado ao motor de voz e o texto limpo com grafia correta enviado para a tela do usuário e salvo no banco de dados.
* Pode alterar **os prompts do Gemini** para gerar outro tipo de respostas ou ciar outro tipode função.
---

## 🚀 Como Reproduzir este Laboratório

Este ambiente foi desenvolvido e testado em uma estação de trabalho Linux (**Lubuntu**). Siga os passos ordenados no terminal para configurá-lo:

### 1. Pré-requisitos do Sistema (Drivers ODBC da Microsoft)

É necessário instalar o Driver 18 para SQL Server e a ferramenta de manipulação de áudio `ffmpeg`:

```bash
# Importar chaves e configurar repositório da Microsoft no Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/24.04/prod noble main" | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Instalar dependências e drivers de sistema
sudo apt update
sudo ACCEPT_EULA=Y apt install -y mssql-tools18 msodbcsql18 unixodbc-dev ffmpeg

```

### 2. Configuração do Ambiente Python

Isole as dependências criando e ativando um ambiente virtual (`venv`):

```bash
# Criar e ativar o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar as bibliotecas necessárias
pip install pyodbc edge-tts google-genai gradio pydub python-dotenv

```

### 3. Configuração do Banco de Dados

Crie as tabelas na sua instância do Azure SQL executando o script de modelagem abaixo. Você pode rodar isso direto pelo terminal usando o `sqlcmd`:

```sql
-- Criar tabela para o histórico de conversação
CREATE TABLE HistoricoConversas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    data_interacao DATETIME DEFAULT GETDATE(),
    texto_usuario NVARCHAR(MAX) NOT NULL,
    resposta_ia NVARCHAR(MAX) NOT NULL
);

```

Execução via terminal:

```bash
sqlcmd -S seu-servidor.database.windows.net -d sua-base-de-dados -U seu_usuario -P sua_senha -Q "CREATE TABLE HistoricoConversas (id INT IDENTITY(1,1) PRIMARY KEY, data_interacao DATETIME DEFAULT GETDATE(), texto_usuario NVARCHAR(MAX) NOT NULL, resposta_ia NVARCHAR(MAX) NOT NULL);"

```
O **sqlcmd** é um utilitário de linha de comando que permite executar consultas, scripts e comandos T-SQL diretamente pelo terminal. 
O **import pyodbc** importa a biblioteca do Python utilizada para conectar a aplicação a bancos de dados por meio de drivers ODBC. Ele serve como a ponte que permite ao script enviar comandos, inserir dados e consultar tabelas diretamente no Azure SQL.
```
> ⚠️ **Nota de Segurança de Rede:** Lembre-se de acessar o Portal do Azure e incluir o endereço IPv4 público da sua máquina local nas regras de Firewall do servidor lógico SQL para evitar erros de *Network Connection Timeout*.

### 4. Variáveis de Ambiente

Crie um arquivo chamado `.env` na raiz do seu projeto para armazenar sua chave de API com segurança:

```env
GEMINI_API_KEY="sua_chave_aqui"

```

### 5. Execução do Projeto

Certifique-se de preencher as variáveis da string de conexão (`conn_str`) no arquivo `app.py` com as credenciais do seu usuário local configurado na Azure e execute:

```bash
python3 app.py

```



O Gradio disponibilizará um endereço de acesso local (`http://127.0.0.1:7860`) e gerará um link público temporário seguro para você testar o Voice Tutor a partir de qualquer dispositivo móvel.


Lembre-se de sempre excluir todos os serviços no Azure e API Gemini para evitar cobranças após  fim dos testes.
Tudo Isso já foi excluido.
---

