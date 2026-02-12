# Extração de Procedimentos do PowerBI

## Opções Disponíveis

### Opção 1: Exportação Manual (Mais Simples)

1. Acesse o PowerBI: https://app.powerbi.com/view?r=eyJrIjoiN2UzZjI1ZDItMDZiOC00ZjNlLWEwZjItNzYyMGI5ZDZkYWI1IiwidCI6IjE2MTMyNTk2LWExMzgtNGM4NS1hYTViLTY0ZDk5YTJlY2U4NyJ9

2. Aplique os filtros:
   - ✅ BPA (Consolidado)
   - ✅ BPA (Individualizado)

3. Clique nos "..." (três pontos) na tabela de procedimentos

4. Selecione "Exportar dados" → "CSV"

5. Salve o arquivo e execute:
   ```bash
   python converter_powerbi_csv.py procedimentos.csv
   ```

### Opção 2: Scraping Automático (Playwright)

**Instalar dependências:**
```bash
pip install playwright pandas openpyxl
playwright install chromium
```

**Executar scraper:**
```bash
python scraper_powerbi.py
```

O script irá:
1. Abrir o navegador automaticamente
2. Carregar o PowerBI
3. Tentar aplicar os filtros
4. Extrair os dados
5. Gerar 3 arquivos:
   - `procedimentos_powerbi.json` - Dados brutos
   - `procedimentos_powerbi.csv` - Planilha
   - `procedimentos_bpa_c_powerbi.json` - Config para o sistema

### Opção 3: Inspecionar Network (Para Devs)

1. Abra o PowerBI no navegador
2. Abra DevTools (F12) → Aba "Network"
3. Filtre por "XHR" ou "Fetch"
4. Aplique os filtros no PowerBI
5. Procure por requisições com `query` ou `executeQueries`
6. Copie a URL e payload
7. Use para fazer requisições diretas

**Exemplo de requisição típica do PowerBI:**
```python
import requests

# URL encontrada no Network
url = "https://wabi-brazil-south-api.analysis.windows.net/public/reports/query"

# Payload (copiar do DevTools)
payload = {
    "queries": [...],
    "serializationSettings": {...}
}

response = requests.post(url, json=payload)
data = response.json()
```

## Estrutura de Dados Esperada

### CSV Exportado
```csv
codigo,descricao,tipo
0301010072,CONSULTA MEDICA EM ATENCAO BASICA,bpa_i
0301010064,CONSULTA DE PROFISSIONAIS DE NIVEL SUPERIOR NA ATENCAO BASICA,bpa_c
```

### JSON Gerado
```json
{
  "bpa_c_geral": ["0301010072", "0301010064", ...],
  "bpa_c_idade": ["0214010015", ...],
  "fonte": "PowerBI - Extraído automaticamente",
  "data_extracao": "2026-01-21T10:30:00"
}
```

## Troubleshooting

### Scraper não encontra filtros
- Execute com `headless=False` para ver o navegador
- Aplique os filtros manualmente
- Pressione Enter no terminal quando pronto

### Dados não são extraídos
- Verifique a aba "Network" do DevTools
- Procure o endpoint real que o PowerBI usa
- Adapte o script para a estrutura específica

### PowerBI pede autenticação
- Use exportação manual
- Ou configure autenticação no script Playwright

## Próximos Passos

Depois de extrair os procedimentos:

1. **Validar dados:**
   ```bash
   python validar_procedimentos.py procedimentos_powerbi.json
   ```

2. **Atualizar sistema:**
   - Copie o JSON gerado para `backend/data/procedimentos_bpa_c.json`
   - Reinicie o backend
   - Os novos procedimentos serão usados na consolidação

3. **Verificar:**
   - Acesse `/api/consolidation/verify-procedure/CODIGO`
   - Confirme que o procedimento está na lista correta
