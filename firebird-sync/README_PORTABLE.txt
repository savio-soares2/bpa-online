=== Firebird Sync Portable ===

Para usar este aplicativo em qualquer computador:

1. Copie a pasta "release" inteira (contendo este arquivo, o .exe e o .json).
2. Certifique-se de que o computador tenha o Firebird instalado e o banco de dados do BPA Online disponível (arquivo .db).

Configuração:
O arquivo "firebird_config.json" deve estar na mesma pasta do executável.
Edite-o para configurar:
- Conexão com o banco Firebird ("database", "user", etc).
- Caminho do banco BPA Online ("bpa_db_path").

Exemplo de firebird_config.json:
{
  "host": "localhost",
  "database": "C:\\BPA\\BPAMAG.GDB",
  "user": "SYSDBA",
  "password": "masterkey",
  "charset": "WIN1252",
  "bpa_db_path": "C:\\Caminho\\Para\\bpa_online.db"
}

Se "bpa_db_path" não for informado, o programa procurará por "bpa_online.db" na mesma pasta do executável.

Execução:
Basta rodar o "FirebirdSync.exe". Ele abrirá uma janela de navegador automaticamente (http://localhost:8001) ou você pode acessar manualmente.
Obs: O executável funciona como um servidor local. Mantenha a janela aberta enquanto usar.
