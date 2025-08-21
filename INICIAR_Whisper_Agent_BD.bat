@ECHO OFF
SETLOCAL

REM Define o caminho absoluto do arquivo de log
SET "LOGFILE=%~dp0Whatsapp_Whispper_Agent_Bd.log"

REM Limpa o log anterior e inicia o novo
ECHO. > "%LOGFILE%"

ECHO ==================================================================
ECHO  INICIANDO SCRIPT DE VERIFICACAO E STARTUP - WHISPER AGENT BD
ECHO ==================================================================
ECHO.
ECHO ================================================================== >> "%LOGFILE%"
ECHO %date% %time% - INICIANDO SCRIPT DE VERIFICACAO E STARTUP >> "%LOGFILE%"
ECHO ================================================================== >> "%LOGFILE%"

ECHO [FASE 1/4] Verificando dependencias...
ECHO %date% %time% - [FASE 1/4] Verificando dependencias... >> "%LOGFILE%"

ECHO [BACKEND] Verificando e instalando dependencias Python (ver log para detalhes)... 
ECHO %date% %time% - [BACKEND] Verificando e instalando dependencias Python... >> "%LOGFILE%"
cd "%~dp0bd_specialist_agent"
pip install -r requirements.txt >> "%LOGFILE%" 2>&1
IF ERRORLEVEL 1 (
    ECHO [ERRO] Falha ao instalar dependencias do backend. Verifique o log %LOGFILE%.
    ECHO %date% %time% - [ERRO] Falha ao instalar dependencias do backend. >> "%LOGFILE%"
    GOTO END
)
ECHO [BACKEND] Dependencias Python OK.
ECHO %date% %time% - [BACKEND] Dependencias Python OK. >> "%LOGFILE%"
cd "%~dp0"
ECHO.

ECHO [FRONTEND] Verificando e instalando dependencias Node.js (ver log para detalhes)...
ECHO %date% %time% - [FRONTEND] Verificando e instalando dependencias Node.js... >> "%LOGFILE%"
cd "%~dp0frontend"
npm install >> "%LOGFILE%" 2>&1
IF ERRORLEVEL 1 (
    ECHO [ERRO] Falha ao instalar dependencias do frontend. Verifique o log %LOGFILE%.
    ECHO %date% %time% - [ERRO] Falha ao instalar dependencias do frontend. >> "%LOGFILE%"
    GOTO END
)
ECHO [FRONTEND] Dependencias Node.js OK.
ECHO %date% %time% - [FRONTEND] Dependencias Node.js OK. >> "%LOGFILE%"
cd "%~dp0"
ECHO.

ECHO [FASE 2/4] Executando testes de inicializacao...
ECHO %date% %time% - [FASE 2/4] Executando testes de inicializacao... >> "%LOGFILE%"

ECHO [BACKEND] Nenhum teste configurado para o backend. Pulando.
ECHO %date% %time% - [BACKEND] Nenhum teste configurado para o backend. Pulando. >> "%LOGFILE%"
ECHO.

ECHO [FRONTEND] Executando testes do frontend (ver log para detalhes)...
ECHO %date% %time% - [FRONTEND] Executando testes do frontend... >> "%LOGFILE%"
cd "%~dp0frontend"
npm test -- --watchAll=false >> "%LOGFILE%" 2>&1
IF ERRORLEVEL 1 (
    ECHO [AVISO] Testes do frontend falharam ou nao foram encontrados.
    ECHO %date% %time% - [AVISO] Testes do frontend falharam ou nao foram encontrados. >> "%LOGFILE%"
) ELSE (
    ECHO [FRONTEND] Testes OK.
    ECHO %date% %time% - [FRONTEND] Testes OK. >> "%LOGFILE%"
)
cd "%~dp0"
ECHO.

ECHO [FASE 3/4] Iniciando aplicacoes...
ECHO %date% %time% - [FASE 3/4] Iniciando aplicacoes... >> "%LOGFILE%"

ECHO [BACKEND] Iniciando servidor backend em http://localhost:8000
ECHO %date% %time% - [BACKEND] Iniciando servidor backend... >> "%LOGFILE%"
cd "%~dp0bd_specialist_agent"
start "Backend - BD Specialist Agent" cmd /c "python run.py" >> "%LOGFILE%" 2>&1
cd "%~dp0"

ECHO [FRONTEND] Iniciando servidor frontend em http://localhost:3000
ECHO %date% %time% - [FRONTEND] Iniciando servidor frontend... >> "%LOGFILE%"
cd "%~dp0frontend"
start "Frontend - BD Specialist Agent" cmd /c "npm start" >> "%LOGFILE%" 2>&1
cd "%~dp0"
ECHO.

ECHO [FASE 4/4] Script de inicializacao concluido.
ECHO %date% %time% - [FASE 4/4] Script de inicializacao concluido. >> "%LOGFILE%"
ECHO Servidores estao rodando em background.
ECHO O log completo foi salvo em: %LOGFILE%
ECHO.

:END
ECHO O script foi concluido. Pressione qualquer tecla para sair.
PAUSE > NUL
