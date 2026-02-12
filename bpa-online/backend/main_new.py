"""
BPA Online API - Sistema de Cadastro e Exportação BPA
Fluxo: Formulário Web → SQLite Local → Exportação SQL → Firebird
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from typing import List, Optional
import uvicorn
from datetime import datetime
import os

from database import BPADatabase, db
from exporter import FirebirdExporter, exporter
from models.schemas import (
    # Profissionais/Pacientes
    ProfissionalCreate, ProfissionalResponse,
    PacienteCreate, PacienteResponse,
    # BPA
    BPAIndividualizadoCreate, BPAIndividualizadoResponse,
    BPAConsolidadoCreate, BPAConsolidadoResponse,
    # Exportação
    ExportRequest, ExportResponse,
    # Procedimentos
    ProcedimentoResponse,
    # Julia
    JuliaImportRequest, JuliaImportResponse,
    # Stats
    BPAStatsResponse,
    DashboardStats
)

app = FastAPI(
    title="BPA Online API",
    description="Sistema de cadastro BPA e exportação para Firebird",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminho dos DBFs
DBF_PATH = os.path.join(os.path.dirname(__file__), '..', 'BPA-main', 'RELATORIOS')


# ========== ENDPOINTS BÁSICOS ==========

@app.get("/")
async def root():
    return {
        "message": "BPA Online API",
        "version": "2.0.0",
        "status": "online",
        "modules": ["formulario", "exportacao", "julia"]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/stats", response_model=BPAStatsResponse)
async def get_stats():
    """Retorna estatísticas gerais do sistema"""
    try:
        stats = db.get_stats()
        return BPAStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Estatísticas para o dashboard"""
    try:
        stats = db.get_stats()
        return DashboardStats(
            total_cnes=len(stats.get('cnes_list', [])),
            total_registros=stats.get('total_bpai', 0) + stats.get('total_bpac', 0),
            cnes_disponiveis=stats.get('cnes_list', [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== PROFISSIONAIS ==========

@app.get("/api/profissionais", response_model=List[ProfissionalResponse])
async def list_profissionais(cnes: Optional[str] = None):
    """Lista profissionais cadastrados"""
    try:
        return db.list_profissionais(cnes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profissionais/{cns}", response_model=ProfissionalResponse)
async def get_profissional(cns: str):
    """Busca profissional pelo CNS"""
    try:
        prof = db.get_profissional(cns)
        if not prof:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")
        return prof
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profissionais", response_model=ProfissionalResponse)
async def create_profissional(data: ProfissionalCreate):
    """Cadastra ou atualiza profissional"""
    try:
        id = db.save_profissional(data.dict())
        return db.get_profissional(data.cns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== PACIENTES ==========

@app.get("/api/pacientes/search")
async def search_pacientes(q: str = Query(..., min_length=2)):
    """Busca pacientes por nome ou CNS"""
    try:
        return db.search_pacientes(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pacientes/{cns}", response_model=PacienteResponse)
async def get_paciente(cns: str):
    """Busca paciente pelo CNS"""
    try:
        pac = db.get_paciente(cns)
        if not pac:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        return pac
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pacientes", response_model=PacienteResponse)
async def create_paciente(data: PacienteCreate):
    """Cadastra ou atualiza paciente"""
    try:
        id = db.save_paciente(data.dict())
        return db.get_paciente(data.cns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== BPA INDIVIDUALIZADO ==========

@app.get("/api/bpa/individualizado")
async def list_bpa_individualizado(
    cnes: str = Query(...),
    competencia: str = Query(...),
    exportado: Optional[bool] = None
):
    """Lista registros BPA-I"""
    try:
        return db.list_bpa_individualizado(cnes, competencia, exportado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bpa/individualizado/count")
async def count_bpa_individualizado(
    cnes: str = Query(...),
    competencia: str = Query(...)
):
    """Conta registros BPA-I"""
    try:
        return db.count_bpa_individualizado(cnes, competencia)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bpa/individualizado/{id}", response_model=BPAIndividualizadoResponse)
async def get_bpa_individualizado(id: int):
    """Busca BPA-I pelo ID"""
    try:
        record = db.get_bpa_individualizado(id)
        if not record:
            raise HTTPException(status_code=404, detail="Registro não encontrado")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bpa/individualizado", response_model=BPAIndividualizadoResponse)
async def create_bpa_individualizado(data: BPAIndividualizadoCreate):
    """Cadastra novo registro BPA-I"""
    try:
        # Salva profissional no cache
        db.save_profissional({
            'cns': data.cns_profissional,
            'cbo': data.cbo,
            'cnes': data.cnes,
            'ine': data.ine
        })
        
        # Salva registro
        id = db.save_bpa_individualizado(data.dict())
        return db.get_bpa_individualizado(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bpa/individualizado/{id}")
async def delete_bpa_individualizado(id: int):
    """Remove registro BPA-I"""
    try:
        if db.delete_bpa_individualizado(id):
            return {"message": "Registro removido com sucesso"}
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== BPA CONSOLIDADO ==========

@app.get("/api/bpa/consolidado")
async def list_bpa_consolidado(
    cnes: str = Query(...),
    competencia: str = Query(...)
):
    """Lista registros BPA-C"""
    try:
        return db.list_bpa_consolidado(cnes, competencia)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bpa/consolidado", response_model=BPAConsolidadoResponse)
async def create_bpa_consolidado(data: BPAConsolidadoCreate):
    """Cadastra registro BPA-C"""
    try:
        id = db.save_bpa_consolidado(data.dict())
        records = db.list_bpa_consolidado(data.cnes, data.competencia)
        return next((r for r in records if r['id'] == id), None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== PROCEDIMENTOS ==========

@app.get("/api/procedimentos/search")
async def search_procedimentos(q: str = Query(..., min_length=2)):
    """Busca procedimentos por código ou descrição"""
    try:
        results = db.search_procedimentos(q)
        
        # Se não encontrou no cache, tenta no DBF
        if not results:
            try:
                from dbfread import DBF
                dbf_file = os.path.join(DBF_PATH, 'S_PA.DBF')
                if os.path.exists(dbf_file):
                    table = DBF(dbf_file, encoding='latin-1')
                    for record in table:
                        codigo = record.get('PA_CODUNI', '').strip()
                        descricao = record.get('PA_DESUNI', '').strip()
                        if q.lower() in codigo.lower() or q.lower() in descricao.lower():
                            results.append({
                                'codigo': codigo,
                                'descricao': descricao,
                                'valor': float(record.get('PA_TOTAL', 0) or 0)
                            })
                            if len(results) >= 30:
                                break
            except Exception as e:
                print(f"[WARN] Erro ao buscar no DBF: {e}")
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/procedimentos/{codigo}", response_model=ProcedimentoResponse)
async def get_procedimento(codigo: str):
    """Busca procedimento pelo código"""
    try:
        # Primeiro tenta no cache
        proc = db.get_procedimento(codigo)
        if proc:
            return proc
        
        # Se não encontrou, busca no DBF
        try:
            from dbfread import DBF
            dbf_file = os.path.join(DBF_PATH, 'S_PA.DBF')
            if os.path.exists(dbf_file):
                table = DBF(dbf_file, encoding='latin-1')
                for record in table:
                    if record.get('PA_CODUNI', '').strip() == codigo:
                        return {
                            'codigo': codigo,
                            'descricao': record.get('PA_DESUNI', '').strip(),
                            'valor': float(record.get('PA_TOTAL', 0) or 0)
                        }
        except Exception as e:
            print(f"[WARN] Erro ao buscar no DBF: {e}")
        
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/procedimentos/import-dbf")
async def import_procedimentos_dbf():
    """Importa procedimentos do DBF para o cache local"""
    try:
        count = db.import_procedimentos_from_dbf(DBF_PATH)
        return {"message": f"Importados {count} procedimentos", "total": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== EXPORTAÇÃO ==========

@app.post("/api/export", response_model=ExportResponse)
async def export_bpa(request: ExportRequest):
    """Exporta BPA para arquivo SQL"""
    try:
        if request.tipo == "BPA-I":
            result = exporter.export_bpai(
                request.cnes, 
                request.competencia,
                request.apenas_nao_exportados
            )
        elif request.tipo == "BPA-C":
            result = exporter.export_bpac(request.cnes, request.competencia)
        else:  # TODOS
            result = exporter.export_all(request.cnes, request.competencia)
        
        if result['filename']:
            result['download_url'] = f"/api/export/download/{result['filename']}"
        
        return ExportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/download/{filename}")
async def download_export(filename: str):
    """Download do arquivo de exportação"""
    try:
        filepath = os.path.join(exporter.output_dir, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        return FileResponse(
            filepath, 
            media_type='application/sql',
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/list")
async def list_exports():
    """Lista arquivos de exportação disponíveis"""
    try:
        return exporter.list_exports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== IMPORTAÇÃO API JULIA ==========

@app.post("/api/julia/import", response_model=JuliaImportResponse)
async def import_from_julia(request: JuliaImportRequest):
    """
    Importa dados da API Julia
    Recebe JSON e salva no banco local
    """
    try:
        imported = 0
        errors = []
        
        for i, registro in enumerate(request.registros):
            try:
                if request.tipo == "BPA-I":
                    # Monta dados para BPA-I
                    data = {
                        'cnes': request.cnes,
                        'competencia': request.competencia,
                        'cns_profissional': registro.get('cns_profissional'),
                        'cbo': registro.get('cbo'),
                        'ine': registro.get('equipe_ine'),
                        'cns_paciente': registro.get('cns_paciente'),
                        'nome_paciente': registro.get('nome_paciente', '')[:30].upper(),
                        'data_nascimento': registro.get('data_nascimento'),
                        'sexo': registro.get('sexo'),
                        'raca_cor': registro.get('raca_cor', '99'),
                        'nacionalidade': registro.get('nacionalidade', '010'),
                        'municipio_ibge': registro.get('municipio_ibge'),
                        'data_atendimento': registro.get('data_atendimento'),
                        'procedimento': registro.get('procedimento'),
                        'quantidade': registro.get('quantidade', 1),
                        'cid': registro.get('cid'),
                        'carater_atendimento': registro.get('carater_atendimento', '01'),
                        'origem': 'BPI'
                    }
                    db.save_bpa_individualizado(data)
                    
                elif request.tipo == "BPA-C":
                    data = {
                        'cnes': request.cnes,
                        'competencia': request.competencia,
                        'cns_profissional': registro.get('cns_profissional'),
                        'cbo': registro.get('cbo'),
                        'procedimento': registro.get('procedimento'),
                        'idade': registro.get('idade', '999'),
                        'quantidade': registro.get('quantidade', 1),
                        'origem': 'BPC'
                    }
                    db.save_bpa_consolidado(data)
                
                imported += 1
                
            except Exception as e:
                errors.append(f"Registro {i+1}: {str(e)}")
        
        return JuliaImportResponse(
            status="success" if not errors else "partial",
            message=f"Importados {imported} de {len(request.registros)} registros",
            total_recebidos=len(request.registros),
            total_importados=imported,
            erros=errors[:10]  # Limita a 10 erros
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== CONFIGURAÇÕES ==========

@app.get("/api/config/{chave}")
async def get_config(chave: str):
    """Obtém configuração"""
    try:
        valor = db.get_config(chave)
        return {"chave": chave, "valor": valor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/{chave}")
async def set_config(chave: str, valor: str):
    """Salva configuração"""
    try:
        db.set_config(chave, valor)
        return {"message": "Configuração salva", "chave": chave, "valor": valor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== DADOS DE REFERÊNCIA ==========

@app.get("/api/referencias/raca-cor")
async def get_racas():
    """Lista códigos de raça/cor"""
    return [
        {"codigo": "01", "descricao": "Branca"},
        {"codigo": "02", "descricao": "Preta"},
        {"codigo": "03", "descricao": "Parda"},
        {"codigo": "04", "descricao": "Amarela"},
        {"codigo": "05", "descricao": "Indígena"},
        {"codigo": "99", "descricao": "Sem informação"}
    ]

@app.get("/api/referencias/sexo")
async def get_sexos():
    """Lista códigos de sexo"""
    return [
        {"codigo": "M", "descricao": "Masculino"},
        {"codigo": "F", "descricao": "Feminino"}
    ]

@app.get("/api/referencias/carater-atendimento")
async def get_carater():
    """Lista códigos de caráter de atendimento"""
    return [
        {"codigo": "01", "descricao": "Eletivo"},
        {"codigo": "02", "descricao": "Urgência"},
        {"codigo": "03", "descricao": "Acidente no local de trabalho"},
        {"codigo": "04", "descricao": "Acidente no trajeto"},
        {"codigo": "05", "descricao": "Outros acidentes"},
        {"codigo": "06", "descricao": "Outros"}
    ]

@app.get("/api/referencias/nacionalidade")
async def get_nacionalidades():
    """Lista principais códigos de nacionalidade"""
    return [
        {"codigo": "010", "descricao": "Brasileiro"},
        {"codigo": "020", "descricao": "Naturalizado Brasileiro"},
        {"codigo": "021", "descricao": "Argentino"},
        {"codigo": "022", "descricao": "Boliviano"},
        {"codigo": "023", "descricao": "Chileno"},
        {"codigo": "024", "descricao": "Paraguaio"},
        {"codigo": "025", "descricao": "Uruguaio"},
        {"codigo": "026", "descricao": "Venezuelano"}
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
