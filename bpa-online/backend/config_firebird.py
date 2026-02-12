import os
from dotenv import load_dotenv

load_dotenv()

class FirebirdConfig:
    """Configuração para conexão com Firebird"""
    
    def __init__(self):
        self.host = os.getenv('FB_HOST', 'localhost')
        self.port = os.getenv('FB_PORT', '3050')
        self.database = os.getenv('FB_DATABASE', 'C:\\BPA\\BPAMAG.GDB')
        self.user = os.getenv('FB_USER', 'SYSDBA')
        self.password = os.getenv('FB_PASSWORD', 'masterkey')
        self.charset = os.getenv('FB_CHARSET', 'UTF8')
    
    def get_connection_string(self) -> str:
        """Retorna string de conexão ODBC"""
        return (
            f"DRIVER={{Firebird/InterBase(r) driver}};"
            f"UID={self.user};PWD={self.password};"
            f"DBNAME={self.host}/{self.port}:{self.database};"
            f"CHARSET={self.charset}"
        )
    
    def validate(self) -> bool:
        """Valida configurações"""
        if not self.password or self.password == 'masterkey':
            print("⚠️ Usando senha padrão do Firebird. Configure FB_PASSWORD no .env")
        return True
