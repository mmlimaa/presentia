@echo off
title Backup Presentia
echo =========================================
echo   BACKUP DO BANCO DE DADOS - PRESENTIA
echo =========================================
echo.

cd /d "%~dp0"

:: Configuracoes do Banco
set PGUSER=presentia_user
set PGDATABASE=presentia
set PGHOST=localhost
set PGPORT=5432
set PGBIN=C:\Program Files\PostgreSQL\17\bin

:: Gera o nome do arquivo com a data e hora atual
set TIMESTAMP=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set FILENAME=backups\backup_%TIMESTAMP%.sql

echo Iniciando backup para: %FILENAME%
echo.

:: Executa o pg_dump com o caminho completo
"%PGBIN%\pg_dump.exe" -U %PGUSER% -h %PGHOST% -p %PGPORT% -F p -f "%FILENAME%" %PGDATABASE%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ? Backup concluido com sucesso!
    echo Arquivo salvo em: %FILENAME%
) else (
    echo.
    echo ? ERRO ao gerar o backup. Codigo: %ERRORLEVEL%
)

echo.
echo Aperte qualquer tecla para sair.
pause > nul
