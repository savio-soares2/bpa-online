# BPA Online API Contract Map

This document tracks the current API surface that must be preserved during the FastAPI -> Django migration.

## Auth
- POST /api/auth/login
- POST /api/auth/register
- GET /api/auth/me

## Admin
- GET /api/admin/users
- POST /api/admin/users
- PUT /api/admin/users/{user_id}
- PUT /api/admin/users/{user_id}/toggle?ativo={bool}
- DELETE /api/admin/users/{user_id}
- POST /api/admin/users/{user_id}/reset-password
- GET /api/admin/cbos
- GET /api/admin/profissionais
- POST /api/admin/profissionais
- DELETE /api/admin/profissionais/{id}
- GET /api/admin/dashboard/stats
- GET /api/admin/database-overview
- GET /api/admin/historico-extracoes
- POST /api/admin/fix-encoding
- DELETE /api/admin/delete-data

## Dashboard
- GET /api/dashboard/stats

## Profissionais
- GET /api/profissionais
- GET /api/profissionais/{cns}
- POST /api/profissionais

## Pacientes
- GET /api/pacientes/search
- GET /api/pacientes/{cns}
- POST /api/pacientes

## Procedimentos
- GET /api/procedures/search
- GET /api/procedimentos/{codigo}
- GET /api/procedimentos/search

## BPA Individualizado
- GET /api/bpa/individualizado
- POST /api/bpa/individualizado
- DELETE /api/bpa/individualizado

## BPA Consolidado
- GET /api/bpa/consolidado
- POST /api/bpa/consolidado

## Exportacao
- POST /api/export
- GET /api/export/list
- GET /api/export/download/{filename}
- POST /api/export/reset

## Julia
- POST /api/julia/import
- POST /api/julia/check-connection

## Referencias
- GET /api/referencias/raca-cor
- GET /api/referencias/sexo
- GET /api/referencias/carater-atendimento

## BiServer
- GET /api/biserver/test-connection
- POST /api/biserver/extract
- POST /api/biserver/extract-profissionais
- GET /api/biserver/count
- POST /api/biserver/extract-and-separate
- POST /api/biserver/extract-all
- POST /api/biserver/extract-pacientes
- GET /api/biserver/export-options

## Consolidacao
- POST /api/consolidation/execute
- GET /api/consolidation/verify-procedure/{codigo}
- GET /api/consolidation/stats

## Reports
- POST /api/reports/generate
- GET /api/reports/list
- GET /api/reports/download/{folder}/{filename}

## SIGTAP
- GET /api/sigtap/competencias
- POST /api/sigtap/competencias
- PUT /api/sigtap/competencias/{competencia}/activate
- GET /api/sigtap/procedimentos
- GET /api/sigtap/estatisticas
- GET /api/sigtap/registros

## Health
- GET /api/health
