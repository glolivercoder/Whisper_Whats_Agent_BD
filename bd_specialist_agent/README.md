# BD Specialist Agent

Agente especialista em banco de dados para atendimento via WhatsApp.

## Descrição

Este projeto implementa um agente de IA que pode interagir com usuários de WhatsApp, receber consultas de áudio, transcrevê-las, e executar consultas em múltiplos bancos de dados para responder às perguntas dos usuários.

## Arquitetura

A arquitetura é baseada em microserviços e inclui:

- **Backend:** FastAPI
- **Agente IA:** LangChain
- **Banco de Dados:** SQLAlchemy para conectar a MySQL, PostgreSQL, Supabase, etc.
- **Transcrição de Áudio (STT):** faster-whisper
- **Síntese de Voz (TTS):** Piper TTS
- **Gateway WhatsApp:** Evolution API

## Como Executar

1.  **Configure o ambiente:**
    - Preencha o arquivo `.env` a partir do `.env.example` com suas credenciais.

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute a aplicação:**
    ```bash
    python run.py
    ```
