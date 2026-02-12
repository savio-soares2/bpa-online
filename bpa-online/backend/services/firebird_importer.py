import firebirdsql
import json
import os
from typing import List, Dict, Any
from config_firebird import FirebirdConfig

class FirebirdImporter:
    """Serviço de importação para banco Firebird (usando firebirdsql - pure Python)"""
    
    def __init__(self):
        self.config = FirebirdConfig()
    
    def connect(self):
        """Conecta ao banco Firebird usando firebirdsql (pure Python, sem dependência de DLLs)"""
        try:
            conn = firebirdsql.connect(
                host=self.config.host,
                port=int(self.config.port),
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                charset=self.config.charset
            )
            return conn
        except Exception as e:
            raise Exception(f"Erro ao conectar no Firebird: {str(e)}")
    
    def import_records(self, records: List[Dict[str, Any]], batch_size: int = 500) -> Dict[str, Any]:
        """
        Importa registros para a tabela S_PRD do Firebird
        
        Args:
            records: Lista de registros para importar
            batch_size: Tamanho do lote de importação
            
        Returns:
            Dicionário com estatísticas da importação
        """
        conn = None
        cursor = None
        total_imported = 0
        errors = []
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Campos da tabela S_PRD
            columns = [
                'prd_uid', 'prd_cmp', 'prd_cnsmed', 'prd_cbo', 'prd_flh', 'prd_seq',
                'prd_pa', 'prd_cnspac', 'prd_nmpac', 'prd_dtnasc', 'prd_sexo',
                'prd_ibge', 'prd_dtaten', 'prd_cid', 'prd_idade', 'prd_qt_p',
                'prd_caten', 'prd_naut', 'prd_org', 'prd_mvm', 'prd_flpa',
                'prd_flcbo', 'prd_flca', 'prd_flida', 'prd_flqt', 'prd_fler',
                'prd_flmun', 'prd_flcid', 'prd_raca', 'prd_servico',
                'prd_classificacao', 'prd_etnia', 'prd_nac', 'prd_advqt',
                'prd_cnpj', 'prd_eqp_area', 'prd_eqp_seq', 'prd_lograd_pcnte',
                'prd_cep_pcnte', 'prd_end_pcnte', 'prd_compl_pcnte',
                'prd_num_pcnte', 'prd_bairro_pcnte', 'prd_ddtel_pcnte',
                'prd_tel_pcnte', 'prd_email_pcnte', 'prd_ine'
            ]
            
            # Processa em lotes
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                for record in batch:
                    try:
                        # Prepara valores
                        values = []
                        for col in columns:
                            val = record.get(col)
                            if val is None or val == 'NULL' or val == '':
                                values.append(None)
                            else:
                                values.append(val)
                        
                        # Monta query INSERT
                        placeholders = ', '.join(['?' for _ in columns])
                        cols_str = ', '.join(columns)
                        query = f"INSERT INTO S_PRD ({cols_str}) VALUES ({placeholders})"
                        
                        # Executa insert
                        cursor.execute(query, values)
                        total_imported += 1
                        
                    except Exception as e:
                        error_msg = f"Erro ao importar registro: {str(e)}"
                        errors.append(error_msg)
                        continue
                
                # Commit a cada lote
                conn.commit()
            
            return {
                'status': 'success',
                'message': f'Importação concluída: {total_imported} registros importados',
                'total_records': len(records),
                'imported': total_imported,
                'errors': len(errors),
                'error_messages': errors[:10]  # Primeiros 10 erros
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Erro durante importação: {str(e)}")
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def execute_procedures(self) -> Dict[str, Any]:
        """Executa procedures de correção após importação"""
        conn = None
        results = {}
        
        procedures = [
            'MIGRA_BPA_C_GERAL',
            'CORRIGE_SEQUENCIA_BPA',
            'CORRIGE_SEQUENCIA_BPI'
        ]
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            for proc_name in procedures:
                try:
                    cursor.execute(f"EXECUTE PROCEDURE {proc_name}")
                    conn.commit()
                    results[proc_name] = 'success'
                except Exception as e:
                    results[proc_name] = f'error: {str(e)}'
            
            cursor.close()
            return results
            
        except Exception as e:
            raise Exception(f"Erro ao executar procedures: {str(e)}")
            
        finally:
            if conn:
                conn.close()
    
    def validate_connection(self) -> bool:
        """Valida conexão com Firebird"""
        try:
            conn = self.connect()
            conn.close()
            return True
        except:
            return False
