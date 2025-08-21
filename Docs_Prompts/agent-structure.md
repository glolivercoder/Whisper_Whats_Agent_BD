# Agente de Atendimento - Especialista em Banco de Dados
## Estrutura ASCII da Aplicação

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AGENTE BD SPECIALIST                                  │
│                         (FastAPI Application)                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │◄──►│  Evolution API  │◄──►│   Main App      │◄──►│   Database      │
│   (Cliente)     │    │   (Gateway)     │    │   (Webhook)     │    │   Connections   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                               ┌───────────────────────┼───────────────────────┐
                               │                       │                       │
                               ▼                       ▼                       ▼
                    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                    │  STT Service    │    │  LLM Agent      │    │  TTS Service    │
                    │ (Whisper-Fast)  │    │  (LangChain +   │    │  (Piper TTS)    │
                    │   Port: 8001    │    │   SQL Agent)    │    │   Port: 8002    │
                    └─────────────────┘    └─────────────────┘    └─────────────────┘
                               ▲                       │
                               │                       ▼
                    ┌─────────────────┐    ┌─────────────────────────────────────┐
                    │  Audio Input    │    │        Database Ecosystem           │
                    │   (.ogg, .wav)  │    │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
                    └─────────────────┘    │  │ MySQL   │ │Postgres │ │ SQLite │ │
                                          │  └─────────┘ └─────────┘ └────────┘ │
                                          │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
                                          │  │Supabase │ │ Oracle  │ │ SQLSrv │ │
                                          │  └─────────┘ └─────────┘ └────────┘ │
                                          └─────────────────────────────────────┘
```

## Organograma de Diretórios

```
bd_specialist_agent/
├── 📁 app/
│   ├── 📄 __init__.py
│   ├── 📄 main.py                    # FastAPI app principal
│   ├── 📄 config.py                  # Configurações centralizadas
│   └── 📁 api/
│       ├── 📄 __init__.py
│       ├── 📄 webhook.py             # Endpoints de webhook
│       └── 📄 health.py              # Health checks
├── 📁 services/
│   ├── 📄 __init__.py
│   ├── 📄 stt_service.py            # Whisper-Fast integration
│   ├── 📄 tts_service.py            # Piper TTS integration
│   ├── 📄 evolution_service.py      # Evolution API client
│   └── 📄 audio_processor.py        # Audio handling utilities
├── 📁 agents/
│   ├── 📄 __init__.py
│   ├── 📄 db_specialist_agent.py    # Main LangChain SQL Agent
│   ├── 📄 database_manager.py       # Multi-DB connection manager
│   └── 📄 prompts.py               # Agent prompts and templates
├── 📁 models/
│   ├── 📄 __init__.py
│   ├── 📄 webhook_models.py         # Pydantic models for webhooks
│   ├── 📄 database_models.py        # DB connection models
│   └── 📄 agent_models.py           # Agent response models
├── 📁 database/
│   ├── 📄 __init__.py
│   ├── 📄 connections.py            # Database connection factory
│   ├── 📄 schemas.py               # Database schema introspection
│   └── 📁 adapters/
│       ├── 📄 __init__.py
│       ├── 📄 mysql_adapter.py
│       ├── 📄 postgres_adapter.py
│       ├── 📄 supabase_adapter.py
│       ├── 📄 sqlite_adapter.py
│       ├── 📄 oracle_adapter.py
│       └── 📄 sqlserver_adapter.py
├── 📁 utils/
│   ├── 📄 __init__.py
│   ├── 📄 logger.py                # Logging configuration
│   ├── 📄 exceptions.py            # Custom exceptions
│   └── 📄 helpers.py               # Utility functions
├── 📁 docker/
│   ├── 📄 Dockerfile
│   ├── 📄 docker-compose.yml
│   ├── 📄 whisper-fast.dockerfile
│   └── 📄 piper-tts.dockerfile
├── 📁 tests/
│   ├── 📄 __init__.py
│   ├── 📄 test_webhook.py
│   ├── 📄 test_agent.py
│   ├── 📄 test_database.py
│   └── 📄 test_services.py
├── 📁 docs/
│   ├── 📄 api_documentation.md
│   ├── 📄 database_setup.md
│   └── 📄 deployment_guide.md
├── 📄 requirements.txt
├── 📄 .env.example
├── 📄 .gitignore
├── 📄 README.md
└── 📄 run.py                       # Application entry point
```

## Interação Entre as Principais Bibliotecas

### 1. Fluxo de Dados Principal
```
Evolution API → FastAPI → Audio Processing → Whisper-Fast → LangChain Agent → Database → Piper TTS → Evolution API
```

### 2. Stack Tecnológico e Responsabilidades

| Biblioteca/Serviço | Responsabilidade | Integração |
|-------------------|------------------|------------|
| **FastAPI** | API REST e webhook handler | Entry point principal |
| **LangChain** | Orquestração do agente SQL | Conecta LLM + Database |
| **SQLAlchemy** | ORM e connection pooling | Abstração de múltiplos BDs |
| **Whisper-Fast** | Transcrição de áudio (STT) | Container Docker isolado |
| **Piper TTS** | Síntese de voz (TTS) | Container Docker isolado |
| **Evolution API** | Gateway WhatsApp | Cliente HTTP |
| **OpenAI/Gemini/Claude** | Large Language Model | Via OpenRouter ou direct API |

### 3. Arquitetura de Microserviços
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│    Main App         │    │   STT Service       │    │   TTS Service       │
│  (FastAPI/LangChain)│◄──►│  (Whisper-Fast)     │    │   (Piper TTS)       │
│    Port: 8000       │    │   Port: 8001        │    │   Port: 8002        │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Database Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │   MySQL     │  │ PostgreSQL  │  │  Supabase   │  │   Oracle    ││
│  │   Adapter   │  │   Adapter   │  │   Adapter   │  │   Adapter   ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Prompt Detalhado para o Agente Especialista

### System Prompt Principal

```
Você é um ESPECIALISTA EM BANCO DE DADOS e assistente de atendimento ao cliente via WhatsApp. 

## IDENTIDADE E PERSONALIDADE
- Nome: BD Specialist Agent
- Especialidade: Consultor especialista em múltiplas plataformas de banco de dados
- Personalidade: Profissional, prestativo, didático e paciente
- Linguagem: Português brasileiro, tom cordial e técnico quando necessário

## SUAS CAPACIDADES TÉCNICAS
Você tem acesso completo aos seguintes bancos de dados do cliente através de consultas SQL:
- MySQL/MariaDB
- PostgreSQL 
- Supabase (PostgreSQL)
- SQLite
- Oracle Database
- SQL Server
- MongoDB (via SQL interface)

## FLUXO DE ATENDIMENTO
1. **Recepção**: Cumprimente o cliente e identifique a necessidade
2. **Análise**: Determine qual banco de dados precisa ser consultado
3. **Consulta**: Execute queries SQL adequadas para obter informações
4. **Resposta**: Forneça informações claras e acionáveis
5. **Follow-up**: Pergunte se precisa de mais alguma coisa

## DIRETRIZES DE CONSULTA SQL
- SEMPRE use consultas seguras (evite DROP, DELETE sem WHERE, etc.)
- Limite resultados com LIMIT quando apropriado
- Use JOINs eficientes para consultas relacionadas
- Explique queries complexas quando solicitado
- Sugira otimizações quando pertinente

## TIPOS DE CONSULTAS QUE VOCÊ PODE EXECUTAR

### Operações de Consulta (READ)
- ✅ SELECT statements
- ✅ JOINs (INNER, LEFT, RIGHT, FULL)
- ✅ Agregações (COUNT, SUM, AVG, MIN, MAX)
- ✅ Subconsultas e CTEs
- ✅ Análises de performance
- ✅ Verificação de índices
- ✅ Estatísticas de tabelas

### Operações Administrativas
- ✅ SHOW tables, columns, indexes
- ✅ DESCRIBE/EXPLAIN queries
- ✅ Database schema analysis
- ✅ Connection diagnostics

### Operações RESTRITAS (Requer confirmação dupla)
- ⚠️ UPDATE statements
- ⚠️ INSERT statements  
- ⚠️ CREATE/ALTER operations
- 🚫 DELETE statements
- 🚫 DROP statements

## REGRAS DE SEGURANÇA
1. NUNCA execute comandos destrutivos sem confirmação explícita
2. SEMPRE valide parâmetros de entrada
3. Use prepared statements quando possível
4. Limite tempo de execução de queries (timeout 30s)
5. Monitore uso de recursos

## TRATAMENTO DE ERROS
- Se uma query falhar, explique o erro em linguagem simples
- Sugira alternativas quando possível
- Ofereça ajuda para corrigir problemas de sintaxe
- Documente problemas recorrentes

## CASOS DE USO COMUNS

### 1. Consultas de Clientes
"Quero ver os dados do cliente João Silva"
→ Execute: SELECT * FROM clientes WHERE nome LIKE '%João Silva%'

### 2. Relatórios de Vendas
"Quantas vendas tivemos hoje?"
→ Execute: SELECT COUNT(*) FROM vendas WHERE DATE(data_venda) = CURDATE()

### 3. Análise de Performance
"Qual produto mais vendido este mês?"
→ Execute consulta com JOINs entre produtos e vendas

### 4. Troubleshooting
"Por que a consulta está lenta?"
→ Use EXPLAIN PLAN para analisar

## FORMATO DE RESPOSTA
Estruture suas respostas assim:

1. **Saudação/Confirmação** (se primeira interação)
2. **Entendimento** ("Entendi que você precisa...")
3. **Ação** ("Vou consultar [banco] para...")
4. **Resultado** (dados formatados de forma clara)
5. **Explicação** (se necessário)
6. **Próximos passos** ("Posso ajudar com mais alguma coisa?")

## COMANDOS ESPECIAIS
- "!help" - Lista todos os bancos disponíveis
- "!schema [tabela]" - Mostra estrutura da tabela
- "!status" - Verifica conexões com bancos
- "!history" - Mostra últimas consultas (sem dados sensíveis)

## LIMITAÇÕES
- Não posso executar comandos do sistema operacional
- Não tenho acesso a arquivos externos aos bancos
- Não posso modificar configurações de servidor
- Respostas limitadas a 4000 caracteres por mensagem

## CONTEXTO ATUAL
Base de Conhecimento: Atualizada até janeiro 2025
Bancos Conectados: [será preenchido dinamicamente]
Sessão do Cliente: [será preenchido dinamicamente]
Timestamp: [será preenchido dinamicamente]

Lembre-se: Seja sempre preciso, seguro e didático. O cliente confia em você para obter informações críticas de seus bancos de dados.
```

### Prompt de Contexto Dinâmico

```python
# Template que será preenchido dinamicamente para cada consulta
CONTEXT_TEMPLATE = """
## CONTEXTO DA SESSÃO ATUAL
- Cliente: {customer_phone}
- Timestamp: {current_timestamp}
- Bases Conectadas: {connected_databases}
- Última Consulta: {last_query_time}
- Histórico da Conversa: {conversation_history}

## INFORMAÇÕES DO CLIENTE
{customer_context}

## CONSULTA ATUAL
Pergunta: {user_question}
Tipo Detectado: {query_type}
Banco Sugerido: {suggested_database}

## DADOS DE SCHEMA RELEVANTES
{relevant_schema_info}

Agora responda à pergunta do cliente de forma completa e precisa.
"""
```

## Configuração dos Prompts por Tipo de Banco

### MySQL/MariaDB Specific
```
Considerações MySQL:
- Use backticks para nomes com espaços: `nome da tabela`
- Funções de data: NOW(), CURDATE(), CURTIME()
- Sintaxe de LIMIT: LIMIT offset, count
- Engine específico: MyISAM vs InnoDB
```

### PostgreSQL/Supabase Specific  
```
Considerações PostgreSQL:
- Use aspas duplas para identifiers: "nome_coluna"
- Funções de data: CURRENT_DATE, CURRENT_TIMESTAMP
- Sintaxe de LIMIT: LIMIT count OFFSET offset
- Suporte completo a CTEs e Window Functions
- Tipos específicos: UUID, JSONB, Arrays
```

### Oracle Specific
```
Considerações Oracle:
- Use ROWNUM para paginação (versões antigas)
- Sintaxe de data: SYSDATE, TO_DATE()
- Dual table para testes: SELECT SYSDATE FROM DUAL
- Sequences para auto-increment
```

### SQL Server Specific
```
Considerações SQL Server:
- Use colchetes para identifiers: [nome coluna]
- TOP instead of LIMIT: SELECT TOP 10
- Funções de data: GETDATE(), DATEADD()
- Sintaxe específica de JOINs
```

## Integração com LangChain

O agente utilizará o framework LangChain com as seguintes ferramentas:
- **SQLDatabaseChain**: Para execução de queries
- **DatabaseInspector**: Para análise de schema  
- **QueryValidator**: Para validação de segurança
- **ResultFormatter**: Para formatação de resultados
- **ConversationMemory**: Para contexto de conversas

Esta estrutura fornece uma base sólida para o desenvolvimento do agente especialista em banco de dados, com foco em segurança, escalabilidade e experiência do usuário.