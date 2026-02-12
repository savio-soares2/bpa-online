from typing import List, Dict, Any
from services.corrections import BPACorrections
from database import get_connection

class InconsistencyService:
    def __init__(self):
        self.corrector = BPACorrections()

    def get_inconsistency_report(self, cnes: str, competencia: str) -> Dict[str, Any]:
        """
        Gera um relatório de inconsistências para um CNES e competência específicos.
        Analisa apenas BPA Individualizado (BPI) por enquanto, pois é onde a maioria das regras se aplica.
        """
        inconsistencies = []
        summary = {
            "total": 0,
            "critical": 0,
            "warnings": 0
        }

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Busca registros BPI
                cursor.execute("""
                    SELECT 
                        id, prd_nmpac, prd_pa, prd_dtaten, prd_cnspac, prd_cbo, prd_cid,
                        prd_raca, prd_sexo, prd_cep_pcnte, prd_ibge, prd_lograd_pcnte,
                        prd_end_pcnte, prd_bairro_pcnte, prd_num_pcnte, prd_qt_p, prd_caten
                    FROM bpa_individualizado
                    WHERE prd_uid = %s AND prd_cmp = %s
                """, (cnes, competencia))
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                for row in rows:
                    record = dict(zip(columns, row))
                    
                    # Adapta nomes para o BPACorrections (que espera nomes amigáveis em alguns casos ou prd_*)
                    # O apply_corrections já lida com prd_*
                    result = self.corrector.apply_corrections(record, tipo='BPI')
                    
                    if result.corrections_applied or result.should_delete:
                        summary["total"] += 1
                        
                        error_type = "critical" if result.should_delete else "warning"
                        if error_type == "critical":
                            summary["critical"] += 1
                        else:
                            summary["warnings"] += 1
                            
                        # Formata a data de YYYYMMDD para YYYY-MM-DD para o frontend
                        raw_date = record.get("prd_dtaten")
                        formatted_date = None
                        if raw_date and len(raw_date) == 8:
                            formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
                        elif raw_date:
                            formatted_date = raw_date

                        inconsistencies.append({
                            "id": record["id"],
                            "paciente": record["prd_nmpac"],
                            "procedimento": record["prd_pa"],
                            "data": formatted_date,
                            "tipo": error_type,
                            "mensagem": result.delete_reason if result.should_delete else "; ".join(result.corrections_applied),
                            "corrections": result.corrections_applied,
                            "should_delete": result.should_delete,
                            "delete_reason": result.delete_reason
                        })
                
                cursor.close()
                
        except Exception as e:
            print(f"Erro ao gerar relatório de inconsistências: {e}")
            raise e

        return {
            "summary": summary,
            "details": inconsistencies
        }

def get_inconsistency_service():
    return InconsistencyService()
