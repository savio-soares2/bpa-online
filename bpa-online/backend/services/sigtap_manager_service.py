import os
import shutil
import zipfile
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SigtapManagerService:
    """
    Gerencia as versões (competências) das tabelas SIGTAP.
    Responsável por armazenamento, listagem e definição da versão ativa.
    """
    
    def __init__(self, root_dir: str = None):
        if root_dir:
            self.base_dir = Path(root_dir)
        else:
            self.base_dir = Path(__file__).parent.parent / 'data' / 'sigtap'
            
        self.config_file = self.base_dir / 'config.json'
        
        # Garantir estrutura inicial
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_config()
        
    def _ensure_config(self):
        """Garante que o arquivo de configuração existe"""
        if not self.config_file.exists():
            default_config = {
                "active_competencia": None,
                "last_update": datetime.now().isoformat()
            }
            self._save_config(default_config)
            
    def _load_config(self) -> Dict:
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar config SIGTAP: {e}")
            return {"active_competencia": None}
            
    def _save_config(self, config: Dict):
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_available_competencias(self) -> List[Dict]:
        """Lista todas as competências instaladas"""
        competencias = []
        
        if not self.base_dir.exists():
            return []
            
        for item in self.base_dir.iterdir():
            if item.is_dir():
                # Espera-se pastas no formato YYYYMM ou nomes descritivos
                # Verifica se contém arquivos essenciais
                if (item / 'tb_procedimento.txt').exists():
                    stats = item.stat()
                    competencias.append({
                        "competencia": item.name,
                        "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        "path": str(item)
                    })
        
        # Ordenar da mais recente para mais antiga (assumindo nomes numéricos YYYYMM)
        competencias.sort(key=lambda x: x['competencia'], reverse=True)
        return competencias

    def get_active_competencia(self) -> Optional[str]:
        """Retorna a competência definida como ativa"""
        config = self._load_config()
        active = config.get("active_competencia")
        
        # Se não houver ativa explícita, tenta a mais recente
        if not active:
            available = self.get_available_competencias()
            if available:
                active = available[0]['competencia']
                self.set_active_competencia(active)
                
        return active

    def set_active_competencia(self, competencia: str):
        """Define a competência ativa"""
        if not (self.base_dir / competencia).exists():
            raise FileNotFoundError(f"Competência {competencia} não encontrada")
            
        config = self._load_config()
        config["active_competencia"] = competencia
        config["last_update"] = datetime.now().isoformat()
        self._save_config(config)
        logger.info(f"Competência ativa alterada para: {competencia}")

    def get_sigtap_dir(self, competencia: str = None) -> str:
        """
        Retorna o caminho absoluto para o diretório da competência.
        Se competencia for None, usa a ativa.
        """
        target = competencia or self.get_active_competencia()
        
        if not target:
            # Fallback para diretório legado se não houver nada no data/sigtap
            legacy_path = Path(__file__).parent.parent.parent / 'BPA-main' / 'TabelaUnificada_202512_v2601161858'
            if legacy_path.exists():
                logger.warning("Usando diretório SIGTAP legado (nenhuma competência importada ainda)")
                return str(legacy_path)
            raise ValueError("Nenhuma tabela SIGTAP disponível. Por favor, importe uma competência.")
            
        path = self.base_dir / target
        if not path.exists():
             raise FileNotFoundError(f"Diretório da competência {target} não encontrado em {path}")
             
        return str(path)

    def import_competencia(self, file_path: str, competencia: str) -> Dict:
        """
        Importa uma nova competência a partir de um arquivo ZIP.
        
        Args:
            file_path: Caminho temporário do arquivo ZIP
            competencia: Nome da competência (ex: 202601)
        """
        target_dir = self.base_dir / competencia
        
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True)
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # Verificação básica
            if not (target_dir / 'tb_procedimento.txt').exists():
                # Tenta procurar em subpasta (caso o zip tenha pasta raiz)
                subdirs = [d for d in target_dir.iterdir() if d.is_dir()]
                if subdirs and (subdirs[0] / 'tb_procedimento.txt').exists():
                    # Move arquivos para cima
                    for f in subdirs[0].iterdir():
                        shutil.move(str(f), str(target_dir))
                    shutil.rmtree(subdirs[0])
                else:
                    raise ValueError("Arquivo tb_procedimento.txt não encontrado no ZIP")
            
            # Define como ativa automaticamente se for a única
            if not self.get_active_competencia():
                self.set_active_competencia(competencia)
                
            return {
                "success": True,
                "competencia": competencia,
                "message": "Importação concluída com sucesso"
            }
            
        except Exception as e:
            # Limpeza em caso de erro
            if target_dir.exists():
                shutil.rmtree(target_dir)
            logger.error(f"Erro ao importar competência: {e}")
            raise e

# Singleton
_sigtap_manager = None

def get_sigtap_manager() -> SigtapManagerService:
    global _sigtap_manager
    if _sigtap_manager is None:
        _sigtap_manager = SigtapManagerService()
    return _sigtap_manager
