import uuid
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.schemas import ProcessStatus, DashboardStats
from services.sql_parser import SQLParser
from services.dbf_manager_service import DBFManagerService
from services.user_service import UserService
import threading
import logging

logger = logging.getLogger(__name__)

class BPAService:
    """Serviço principal para gerenciamento de extrações BPA"""
    
    def __init__(self):
        self.tasks: Dict[str, ProcessStatus] = {}
        self.sql_parser = SQLParser()
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Diretório para logs
        self.logs_dir = os.path.join(self.data_dir, 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Serviços DBF e Usuários
        self.dbf_manager = DBFManagerService()
        self.user_service = UserService()
    
    def _log(self, task_id: str, level: str, message: str):
        """Registra log de uma tarefa"""
        log_file = os.path.join(self.logs_dir, f"{task_id}.log")
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"[{task_id}] {log_entry.strip()}")
    
    def start_test_extraction(
        self,
        cnes_list: List[str],
        competencia_inicial: str,
        competencia_final: str
    ) -> str:
        """Inicia extração em modo teste usando arquivo SQL"""
        task_id = str(uuid.uuid4())
        
        # Cria status inicial
        status = ProcessStatus(
            task_id=task_id,
            status="pending",
            progress=0,
            message="Iniciando extração...",
            started_at=datetime.now(),
            completed_at=None,
            total_records=0,
            processed_records=0,
            errors=[]
        )
        
        self.tasks[task_id] = status
        self._log(task_id, "INFO", f"Iniciando extração para CNES: {cnes_list}")
        
        # Inicia processamento em thread separada
        thread = threading.Thread(
            target=self._process_test_extraction,
            args=(task_id, cnes_list, competencia_inicial, competencia_final)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _process_test_extraction(
        self,
        task_id: str,
        cnes_list: List[str],
        competencia_inicial: str,
        competencia_final: str
    ):
        """Processa extração em modo teste"""
        try:
            status = self.tasks[task_id]
            status.status = "processing"
            status.message = "Processando dados..."
            
            self._log(task_id, "INFO", "Iniciando processamento")
            
            # Gera lista de competências
            competencias = self._get_competencias_range(
                competencia_inicial,
                competencia_final
            )
            
            all_records = []
            total_expected = len(cnes_list) * len(competencias)
            processed = 0
            
            # Para cada CNES e competência
            for cnes in cnes_list:
                for comp in competencias:
                    self._log(task_id, "INFO", f"Processando CNES {cnes}, competência {comp}")
                    
                    # Busca registros
                    records = self.sql_parser.get_records_by_cnes_competencia(cnes, comp)
                    
                    if records:
                        all_records.extend(records)
                        status.total_records = len(all_records)
                        self._log(
                            task_id,
                            "INFO",
                            f"Encontrados {len(records)} registros para CNES {cnes}, competência {comp}"
                        )
                    else:
                        self._log(
                            task_id,
                            "WARNING",
                            f"Nenhum registro encontrado para CNES {cnes}, competência {comp}"
                        )
                    
                    processed += 1
                    status.processed_records = processed
                    status.progress = int((processed / total_expected) * 100)
                    status.message = f"Processado {processed}/{total_expected}"
            
            # Salva dados processados
            output_file = os.path.join(self.data_dir, f"{task_id}_data.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)
            
            self._log(task_id, "INFO", f"Dados salvos: {len(all_records)} registros")
            
            # Atualiza status final
            status.status = "completed"
            status.progress = 100
            status.message = f"Extração concluída: {len(all_records)} registros"
            status.completed_at = datetime.now()
            
            self._log(task_id, "INFO", "Extração concluída com sucesso")
            
        except Exception as e:
            self._log(task_id, "ERROR", f"Erro durante extração: {str(e)}")
            status = self.tasks.get(task_id)
            if status:
                status.status = "error"
                status.message = f"Erro: {str(e)}"
                status.errors.append(str(e))
                status.completed_at = datetime.now()
    
    def _get_competencias_range(self, inicio: str, fim: str) -> List[str]:
        """Gera lista de competências no intervalo"""
        from dateutil.relativedelta import relativedelta
        
        start = datetime.strptime(inicio, "%Y-%m")
        end = datetime.strptime(fim, "%Y-%m")
        
        competencias = []
        current = start
        while current <= end:
            competencias.append(current.strftime("%Y-%m"))
            current += relativedelta(months=1)
        
        return competencias
    
    def get_task_status(self, task_id: str) -> Optional[ProcessStatus]:
        """Retorna status de uma tarefa"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[ProcessStatus]:
        """Retorna lista de todas as tarefas"""
        return list(self.tasks.values())
    
    def get_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retorna os dados processados de uma tarefa"""
        status = self.tasks.get(task_id)
        if not status:
            return None
        
        # Carrega dados processados
        data_file = os.path.join(self.data_dir, f"{task_id}_data.json")
        if not os.path.exists(data_file):
            return None
        
        with open(data_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        return {
            'task_id': task_id,
            'status': status.status,
            'total_records': len(records),
            'records': records
        }
    
    def get_task_logs(self, task_id: str) -> List[str]:
        """Retorna logs de uma tarefa"""
        log_file = os.path.join(self.logs_dir, f"{task_id}.log")
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.readlines()
        
        return []
    
    def get_dashboard_stats(self) -> DashboardStats:
        """Retorna estatísticas do dashboard"""
        cnes_list = self.sql_parser.get_available_cnes()
        
        total_registros = sum(c.total_registros for c in cnes_list)
        
        tarefas_ativas = sum(1 for t in self.tasks.values() if t.status in ["pending", "processing"])
        tarefas_completas = sum(1 for t in self.tasks.values() if t.status == "completed")
        tarefas_com_erro = sum(1 for t in self.tasks.values() if t.status == "error")
        
        # Última extração
        ultima = None
        if self.tasks:
            completed_tasks = [t for t in self.tasks.values() if t.completed_at]
            if completed_tasks:
                ultima = max(t.completed_at for t in completed_tasks)
        
        return DashboardStats(
            total_cnes=len(cnes_list),
            total_registros=total_registros,
            tarefas_ativas=tarefas_ativas,
            tarefas_completas=tarefas_completas,
            tarefas_com_erro=tarefas_com_erro,
            ultima_extracao=ultima,
            cnes_disponiveis=[c.cnes for c in cnes_list]
        )
    
    def import_to_firebird(self, task_id: str) -> Dict[str, Any]:
        """Importa dados processados para o Firebird"""
        status = self.tasks.get(task_id)
        if not status:
            raise ValueError("Task não encontrada")
        
        if status.status != "completed":
            raise ValueError("Task ainda não foi completada")
        
        self._log(task_id, "INFO", "Iniciando importação para Firebird")
        
        # Carrega dados processados
        data_file = os.path.join(self.data_dir, f"{task_id}_data.json")
        if not os.path.exists(data_file):
            raise ValueError("Arquivo de dados não encontrado")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        # TODO: Implementar importação real para Firebird
        # Por enquanto, apenas simula
        self._log(task_id, "INFO", f"Simulando importação de {len(records)} registros")
        
        return {
            "status": "success",
            "message": f"Importação simulada de {len(records)} registros",
            "records_imported": len(records)
        }
    
    def delete_task(self, task_id: str):
        """Remove uma tarefa e seus dados"""
        # Remove dados
        data_file = os.path.join(self.data_dir, f"{task_id}_data.json")
        if os.path.exists(data_file):
            os.remove(data_file)
        
        # Remove logs
        log_file = os.path.join(self.logs_dir, f"{task_id}.log")
        if os.path.exists(log_file):
            os.remove(log_file)
        
        # Remove do dicionário
        if task_id in self.tasks:
            del self.tasks[task_id]

    # ========== NOVOS MÉTODOS PARA VALIDAÇÃO CBO ==========
    
    def validate_procedure_for_user(self, user_id: int, codigo_procedimento: str) -> Dict[str, Any]:
        """
        Valida se um usuário pode executar um procedimento específico
        
        Args:
            user_id: ID do usuário
            codigo_procedimento: Código do procedimento
            
        Returns:
            Dict com resultado da validação
        """
        try:
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                return {
                    'valido': False,
                    'motivo': 'Usuário não encontrado',
                    'user_id': user_id,
                    'codigo_procedimento': codigo_procedimento
                }
            
            # Valida CBO x Procedimento
            valido = self.dbf_manager.validate_cbo_procedimento(user.cbo, codigo_procedimento)
            
            if not valido:
                return {
                    'valido': False,
                    'motivo': f'CBO {user.cbo} não autorizado para procedimento {codigo_procedimento}',
                    'user_id': user_id,
                    'codigo_procedimento': codigo_procedimento,
                    'cbo': user.cbo
                }
            
            # Obtém informações do procedimento
            proc_info = self.dbf_manager.get_procedimentos_info().get(codigo_procedimento)
            
            return {
                'valido': True,
                'user_id': user_id,
                'codigo_procedimento': codigo_procedimento,
                'cbo': user.cbo,
                'procedimento_info': proc_info,
                'motivo': 'Validação aprovada'
            }
            
        except Exception as e:
            logger.error(f"Erro na validação CBO: {e}")
            return {
                'valido': False,
                'motivo': f'Erro interno: {str(e)}',
                'user_id': user_id,
                'codigo_procedimento': codigo_procedimento
            }
    
    def get_user_procedures(self, user_id: int) -> Dict[str, Any]:
        """
        Obtém lista de procedimentos permitidos para um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com procedimentos e informações
        """
        try:
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'Usuário não encontrado',
                    'user_id': user_id
                }
            
            # Obtém procedimentos permitidos
            procedimentos_codes = self.dbf_manager.get_procedimentos_for_cbo(user.cbo)
            
            # Obtém informações detalhadas dos procedimentos
            procedimentos_info = self.dbf_manager.get_procedimentos_info()
            
            procedimentos_detalhados = []
            for code in procedimentos_codes:
                info = procedimentos_info.get(code, {})
                procedimentos_detalhados.append({
                    'codigo': code,
                    'descricao': info.get('descricao', 'Descrição não encontrada'),
                    'complexidade': info.get('complexidade', ''),
                    'classificacao': info.get('classificacao', ''),
                    'valor_sa': info.get('valor_sa', 0.0)
                })
            
            # Ordena por código
            procedimentos_detalhados.sort(key=lambda x: x['codigo'])
            
            return {
                'success': True,
                'user_id': user_id,
                'cbo': user.cbo,
                'total_procedimentos': len(procedimentos_detalhados),
                'procedimentos': procedimentos_detalhados
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter procedimentos do usuário: {e}")
            return {
                'success': False,
                'message': f'Erro interno: {str(e)}',
                'user_id': user_id
            }
    
    def get_cbos_for_procedure(self, codigo_procedimento: str) -> Dict[str, Any]:
        """
        Obtém lista de CBOs que podem executar um procedimento
        
        Args:
            codigo_procedimento: Código do procedimento
            
        Returns:
            Dict com CBOs permitidos
        """
        try:
            cbos_permitidos = self.dbf_manager.get_cbos_for_procedimento(codigo_procedimento)
            
            # Obtém informações do procedimento
            proc_info = self.dbf_manager.get_procedimentos_info().get(codigo_procedimento)
            
            if not proc_info:
                return {
                    'success': False,
                    'message': 'Procedimento não encontrado',
                    'codigo_procedimento': codigo_procedimento
                }
            
            return {
                'success': True,
                'codigo_procedimento': codigo_procedimento,
                'procedimento_info': proc_info,
                'total_cbos': len(cbos_permitidos),
                'cbos_permitidos': cbos_permitidos
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter CBOs para procedimento: {e}")
            return {
                'success': False,
                'message': f'Erro interno: {str(e)}',
                'codigo_procedimento': codigo_procedimento
            }
    
    def search_procedures(self, query: str, user_id: Optional[int] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Busca procedimentos por código ou descrição
        
        Args:
            query: Termo de busca
            user_id: Se informado, filtra apenas procedimentos permitidos para o usuário
            limit: Limite de resultados
            
        Returns:
            Dict com resultados da busca
        """
        try:
            procedimentos_info = self.dbf_manager.get_procedimentos_info()
            
            # Se user_id informado, filtra apenas procedimentos permitidos
            if user_id:
                user = self.user_service.get_user_by_id(user_id)
                if user:
                    procedimentos_permitidos = set(self.dbf_manager.get_procedimentos_for_cbo(user.cbo))
                    procedimentos_info = {k: v for k, v in procedimentos_info.items() if k in procedimentos_permitidos}
            
            # Busca por código ou descrição
            query_upper = query.upper()
            resultados = []
            
            for codigo, info in procedimentos_info.items():
                match = False
                
                # Busca por código
                if query_upper in codigo:
                    match = True
                
                # Busca por descrição
                if query_upper in info.get('descricao', '').upper():
                    match = True
                
                if match:
                    resultados.append({
                        'codigo': codigo,
                        'descricao': info.get('descricao', ''),
                        'complexidade': info.get('complexidade', ''),
                        'classificacao': info.get('classificacao', ''),
                        'valor_sa': info.get('valor_sa', 0.0)
                    })
                    
                    if len(resultados) >= limit:
                        break
            
            # Ordena por relevância (código primeiro, depois descrição)
            resultados.sort(key=lambda x: (
                0 if query_upper in x['codigo'] else 1,
                x['codigo']
            ))
            
            return {
                'success': True,
                'query': query,
                'total_encontrados': len(resultados),
                'limit': limit,
                'resultados': resultados
            }
            
        except Exception as e:
            logger.error(f"Erro na busca de procedimentos: {e}")
            return {
                'success': False,
                'message': f'Erro interno: {str(e)}',
                'query': query
            }
    
    def get_dbf_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos dados DBF
        
        Returns:
            Dict com estatísticas
        """
        try:
            stats = self.dbf_manager.get_statistics()
            
            return {
                'success': True,
                'statistics': stats,
                'cache_ativo': self.dbf_manager._cache_timestamp is not None,
                'data_atualizacao': self.dbf_manager._cache_timestamp.isoformat() if self.dbf_manager._cache_timestamp else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas DBF: {e}")
            return {
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }
    
    def refresh_dbf_data(self) -> Dict[str, Any]:
        """
        Força atualização dos dados DBF
        
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Iniciando atualização dos dados DBF...")
            self.dbf_manager.refresh_data()
            
            stats = self.dbf_manager.get_statistics()
            
            return {
                'success': True,
                'message': 'Dados DBF atualizados com sucesso',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dados DBF: {e}")
            return {
                'success': False,
                'message': f'Erro ao atualizar dados DBF: {str(e)}'
            }
