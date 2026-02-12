from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import os
import sys

# Adiciona o diretório scripts ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'BPA-main', 'scripts'))

from services.bpa_service import BPAService
from services.sql_parser import SQLParser
from services.firebird_importer import FirebirdImporter
from services.report_generator import BPAReportGenerator, FirebirdDataSource, DBFReader
from models.schemas import (
    ExtractionRequest,
    ExtractionResponse,
    ProcessStatus,
    CNESInfo,
    DashboardStats,
    FirebirdImportRequest,
    FirebirdImportResponse,
    FirebirdConfigRequest,
    ReportGenerateRequest,
    ReportGenerateResponse
)

app = FastAPI(
    title="BPA Online API",
    description="API para automação do fluxo BPA - e-SUS para Firebird",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância do serviço
bpa_service = BPAService()
sql_parser = SQLParser()
firebird_importer = FirebirdImporter()

@app.get("/")
async def root():
    return {
        "message": "BPA Online API",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/api/health")
async def health_check():
    """Verificação de saúde da API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/cnes/list", response_model=List[CNESInfo])
async def list_cnes():
    """Lista todos os CNES disponíveis nos dados de teste"""
    try:
        cnes_list = sql_parser.get_available_cnes()
        return cnes_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cnes/{cnes}/stats")
async def get_cnes_stats(cnes: str):
    """Obtém estatísticas de um CNES específico"""
    try:
        stats = sql_parser.get_cnes_stats(cnes)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Retorna estatísticas gerais do dashboard"""
    try:
        stats = bpa_service.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """
    Inicia extração de dados BPA
    Modo TEST: usa dados do arquivo SQL
    Modo ESUS: conecta ao banco e-SUS (futuro)
    """
    try:
        if request.mode == "TEST":
            # Usa dados do arquivo SQL de teste
            task_id = bpa_service.start_test_extraction(
                cnes_list=request.cnes_list,
                competencia_inicial=request.competencia_inicial,
                competencia_final=request.competencia_final
            )
        else:
            # Futura implementação com banco e-SUS
            raise HTTPException(
                status_code=501,
                detail="Modo ESUS não implementado ainda. Use modo TEST."
            )
        
        return ExtractionResponse(
            task_id=task_id,
            status="started",
            message=f"Extração iniciada para {len(request.cnes_list)} CNES"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/extract/{task_id}/status", response_model=ProcessStatus)
async def get_extraction_status(task_id: str):
    """Retorna o status de uma extração em andamento"""
    try:
        status = bpa_service.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task não encontrada")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks", response_model=List[ProcessStatus])
async def list_tasks():
    """Lista todas as tarefas"""
    try:
        return bpa_service.list_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/firebird/import/{task_id}", response_model=FirebirdImportResponse)
async def import_to_firebird(task_id: str, config: Optional[FirebirdConfigRequest] = None):
    """Importa dados processados para o Firebird"""
    try:
        # Obtém dados da task
        task_data = bpa_service.get_task_data(task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail="Task não encontrada")
        
        # Importa para Firebird
        result = firebird_importer.import_records(task_data.get('records', []))
        
        # Executa procedures se importação bem sucedida
        if result['status'] == 'success':
            proc_results = firebird_importer.execute_procedures()
            result['procedures'] = proc_results
        
        return FirebirdImportResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/firebird/validate")
async def validate_firebird_connection(config: Optional[FirebirdConfigRequest] = None):
    """Valida conexão com Firebird"""
    try:
        is_valid = firebird_importer.validate_connection()
        return {
            "valid": is_valid,
            "message": "Conexão válida" if is_valid else "Falha na conexão"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e)
        }

@app.get("/api/logs/{task_id}")
async def get_task_logs(task_id: str):
    """Retorna os logs de uma tarefa específica"""
    try:
        logs = bpa_service.get_task_logs(task_id)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Remove uma tarefa e seus dados"""
    try:
        bpa_service.delete_task(task_id)
        return {"message": "Task removida com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENDPOINTS DE RELATÓRIOS ==========

DBF_PATH = os.path.join(os.path.dirname(__file__), '..', 'BPA-main', 'RELATORIOS')


@app.post("/api/reports/generate", response_model=ReportGenerateResponse)
async def generate_report(request: ReportGenerateRequest):
    """
    Gera relatório BPA diretamente dos dados do Firebird + DBFs
    Elimina necessidade do software BPA
    """
    try:
        print(f"[LOG] Iniciando geração de relatório...")
        print(f"[LOG] CNES: {request.cnes}, Competência: {request.competencia}, Tipo: {request.tipo_relatorio}")
        
        # Inicializa gerador
        print(f"[LOG] DBF_PATH: {DBF_PATH}")
        generator = BPAReportGenerator(DBF_PATH)
        print(f"[LOG] Generator criado")
        
        data_source = FirebirdDataSource()
        print(f"[LOG] DataSource criado")
        
        # Busca dados
        print(f"[LOG] Buscando registros no Firebird...")
        records = data_source.get_records(request.cnes, request.competencia)
        print(f"[LOG] Registros encontrados: {len(records) if records else 0}")
        
        if not records:
            return ReportGenerateResponse(
                status="warning",
                message="Nenhum registro encontrado para os parâmetros informados",
                total_records=0
            )
        
        # Mostra primeiro registro para debug
        if records:
            print(f"[LOG] Primeiro registro: {list(records[0].keys())}")
            print(f"[LOG] PRD_PA do primeiro: {records[0].get('PRD_PA')}")
        
        # Gera relatório baseado no tipo
        tipo = request.tipo_relatorio or "BPA-I"
        print(f"[LOG] Tipo relatório: {tipo}")
        
        if tipo == "BPA-I":
            print(f"[LOG] Gerando BPA-I...")
            report = generator.generate_bpai_report(records, request.cnes, request.competencia)
            print(f"[LOG] Relatório gerado, tamanho: {len(report) if report else 0}")
        else:
            return ReportGenerateResponse(
                status="error",
                message=f"Tipo de relatório '{tipo}' não implementado ainda"
            )
        
        # Calcula estatísticas
        print(f"[LOG] Calculando estatísticas...")
        professionals = len(set((r.get('PRD_CNSMED'), r.get('PRD_CBO')) for r in records))
        print(f"[LOG] Profissionais: {professionals}")
        
        # Calcula valor total
        print(f"[LOG] Calculando valor total...")
        dbf_reader = DBFReader(DBF_PATH)
        total_value = 0.0
        for r in records:
            pa = r.get('PRD_PA') or ''
            qt = r.get('PRD_QT_P') or 0
            val = dbf_reader.get_procedimento_valor(pa)
            total_value += val * int(qt)
        print(f"[LOG] Valor total: {total_value}")
        
        filename = f"BPA{tipo.replace('-', '')}_{request.cnes}_{request.competencia}.TXT"
        print(f"[LOG] Filename: {filename}")
        
        return ReportGenerateResponse(
            status="success",
            message="Relatório gerado com sucesso",
            filename=filename,
            content=report,
            total_records=len(records),
            total_professionals=professionals,
            total_value=round(total_value, 2)
        )
    except Exception as e:
        import traceback
        print(f"[ERROR] Erro: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/download/{cnes}/{competencia}")
async def download_report(cnes: str, competencia: str, tipo: str = "BPA-I"):
    """Baixa relatório em formato TXT"""
    try:
        generator = BPAReportGenerator(DBF_PATH)
        data_source = FirebirdDataSource()
        
        records = data_source.get_records(cnes, competencia)
        if not records:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado")
        
        if tipo == "BPA-I":
            report = generator.generate_bpai_report(records, cnes, competencia)
        else:
            raise HTTPException(status_code=400, detail=f"Tipo '{tipo}' não suportado")
        
        filename = f"BPA{tipo.replace('-', '')}_{cnes}_{competencia}.TXT"
        
        return PlainTextResponse(
            content=report,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dbf/procedimento/{codigo}")
async def get_procedimento(codigo: str):
    """Busca informações de procedimento no DBF"""
    try:
        dbf_reader = DBFReader(DBF_PATH)
        proc = dbf_reader.get_procedimento(codigo)
        
        if not proc:
            raise HTTPException(status_code=404, detail="Procedimento não encontrado")
        
        return {
            "codigo": codigo,
            "pa_id": proc.get('PA_ID'),
            "pa_dv": proc.get('PA_DV'),
            "valor": proc.get('PA_TOTAL', 0),
            "descricao": proc.get('PA_DC', ''),
            "competencia": proc.get('PA_CMP', '')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dbf/list")
async def list_dbf_files():
    """Lista arquivos DBF disponíveis"""
    try:
        files = []
        if os.path.exists(DBF_PATH):
            for f in os.listdir(DBF_PATH):
                if f.upper().endswith('.DBF'):
                    path = os.path.join(DBF_PATH, f)
                    files.append({
                        "name": f,
                        "size": os.path.getsize(path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
                    })
        return {"dbf_path": DBF_PATH, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/firebird/records/{cnes}/{competencia}")
async def get_firebird_records(cnes: str, competencia: str, limit: int = 100):
    """Lista registros de produção do Firebird"""
    try:
        data_source = FirebirdDataSource()
        records = data_source.get_records(cnes, competencia)
        
        # Limita quantidade
        records = records[:limit]
        
        return {
            "cnes": cnes,
            "competencia": competencia,
            "total": len(records),
            "records": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
