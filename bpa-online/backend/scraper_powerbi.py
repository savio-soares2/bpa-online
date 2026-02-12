"""
Script para extrair dados de procedimentos do PowerBI
Usa Playwright para automação de navegador
"""
import asyncio
from playwright.async_api import async_playwright
import json
import pandas as pd
from datetime import datetime

class PowerBIScraperBPA:
    def __init__(self):
        self.url = "https://app.powerbi.com/view?r=eyJrIjoiN2UzZjI1ZDItMDZiOC00ZjNlLWEwZjItNzYyMGI5ZDZkYWI1IiwidCI6IjE2MTMyNTk2LWExMzgtNGM4NS1hYTViLTY0ZDk5YTJlY2U4NyJ9"
        self.procedimentos = []
    
    async def extrair_procedimentos(self, headless=False):
        """
        Extrai procedimentos do PowerBI
        
        Args:
            headless: Se True, roda sem abrir navegador visível
        """
        async with async_playwright() as p:
            # Abre navegador
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            print("🌐 Abrindo PowerBI...")
            await page.goto(self.url, wait_until='networkidle')
            
            # Aguarda carregar
            await asyncio.sleep(5)
            
            print("📊 PowerBI carregado, procurando filtros...")
            
            # Tenta encontrar e clicar nos checkboxes
            try:
                # Procura por "Seleções múltiplas" ou filtros
                await page.click('text=Seleções múltiplas', timeout=5000)
                await asyncio.sleep(1)
                
                # Marca BPA Consolidado e Individualizado
                await page.click('text=BPA (Consolidado)')
                await page.click('text=BPA (Individualizado)')
                await asyncio.sleep(2)
                
                print("✅ Filtros aplicados")
            except Exception as e:
                print(f"⚠️ Não conseguiu aplicar filtros automaticamente: {e}")
                print("💡 Continue manualmente e pressione Enter quando filtrar...")
                input()
            
            # Aguarda carregar dados filtrados
            await asyncio.sleep(3)
            
            # Tenta encontrar tabela de procedimentos
            print("🔍 Procurando dados de procedimentos...")
            
            # Opção 1: Interceptar requisições de rede
            procedimentos_data = await self._interceptar_dados_rede(page)
            
            if procedimentos_data:
                print(f"✅ Encontrados {len(procedimentos_data)} procedimentos")
                self.procedimentos = procedimentos_data
            else:
                # Opção 2: Extrair visualmente da tabela
                print("🔍 Tentando extrair visualmente...")
                procedimentos_data = await self._extrair_visual(page)
                self.procedimentos = procedimentos_data
            
            # Salva screenshot para debug
            await page.screenshot(path='powerbi_screenshot.png')
            print("📸 Screenshot salvo: powerbi_screenshot.png")
            
            await browser.close()
            
            return self.procedimentos
    
    async def _interceptar_dados_rede(self, page):
        """Intercepta requisições de rede do PowerBI para pegar dados JSON"""
        dados = []
        
        # Escuta requisições
        async def handle_response(response):
            try:
                if 'query' in response.url or 'api' in response.url:
                    if response.status == 200:
                        try:
                            json_data = await response.json()
                            # PowerBI geralmente retorna dados em results > data > dsr > DS > PH ou similar
                            if 'results' in json_data:
                                dados.append(json_data)
                                print(f"✅ Interceptado: {response.url[:100]}...")
                        except:
                            pass
            except:
                pass
        
        page.on('response', handle_response)
        
        # Aguarda um pouco para interceptar
        await asyncio.sleep(5)
        
        # Processa dados interceptados
        procedimentos = self._processar_dados_powerbi(dados)
        return procedimentos
    
    def _processar_dados_powerbi(self, raw_data):
        """Processa dados brutos do PowerBI"""
        procedimentos = []
        
        for item in raw_data:
            try:
                # Navega na estrutura típica do PowerBI
                if 'results' in item:
                    for result in item['results']:
                        if 'result' in result and 'data' in result['result']:
                            data = result['result']['data']
                            
                            # Extrai dados conforme estrutura
                            if 'dsr' in data:
                                dsr = data['dsr']
                                if 'DS' in dsr:
                                    for ds in dsr['DS']:
                                        if 'PH' in ds:  # Primary Hierarchy
                                            for ph_item in ds['PH']:
                                                if 'DM0' in ph_item:  # Data Matrix
                                                    for row in ph_item['DM0']:
                                                        proc = self._extrair_procedimento(row)
                                                        if proc:
                                                            procedimentos.append(proc)
            except Exception as e:
                print(f"⚠️ Erro ao processar item: {e}")
        
        return procedimentos
    
    def _extrair_procedimento(self, row):
        """Extrai informações de procedimento de uma linha"""
        try:
            # Adaptar conforme estrutura real
            return {
                'codigo': row.get('C', [''])[0],  # Código
                'descricao': row.get('C', ['', ''])[1] if len(row.get('C', [])) > 1 else '',
                'tipo': 'bpa_c' if 'consolidado' in str(row).lower() else 'bpa_i'
            }
        except:
            return None
    
    async def _extrair_visual(self, page):
        """Extrai dados visualmente da tabela renderizada"""
        procedimentos = []
        
        try:
            # Procura por tabelas visíveis
            tabelas = await page.query_selector_all('table, .pivotTable, [role="grid"]')
            
            for tabela in tabelas:
                linhas = await tabela.query_selector_all('tr, [role="row"]')
                
                for linha in linhas:
                    colunas = await linha.query_selector_all('td, [role="gridcell"]')
                    
                    if len(colunas) >= 2:
                        codigo = await colunas[0].text_content()
                        descricao = await colunas[1].text_content()
                        
                        if codigo and descricao:
                            procedimentos.append({
                                'codigo': codigo.strip(),
                                'descricao': descricao.strip(),
                                'tipo': 'bpa_i'  # Ajustar conforme necessário
                            })
        except Exception as e:
            print(f"⚠️ Erro na extração visual: {e}")
        
        return procedimentos
    
    def salvar_json(self, filename='procedimentos_powerbi.json'):
        """Salva procedimentos em JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.procedimentos, f, ensure_ascii=False, indent=2)
        print(f"💾 Salvo: {filename}")
    
    def salvar_csv(self, filename='procedimentos_powerbi.csv'):
        """Salva procedimentos em CSV"""
        if self.procedimentos:
            df = pd.DataFrame(self.procedimentos)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"💾 Salvo: {filename}")
    
    def gerar_json_config(self, filename='procedimentos_bpa_c_powerbi.json'):
        """Gera JSON no formato usado pelo sistema"""
        config = {
            "bpa_c_geral": [],
            "bpa_c_idade": [],
            "fonte": "PowerBI - Extraído automaticamente",
            "data_extracao": datetime.now().isoformat()
        }
        
        for proc in self.procedimentos:
            codigo = proc.get('codigo', '').strip()
            if codigo and codigo.isdigit():
                if proc.get('tipo') == 'bpa_c':
                    config['bpa_c_geral'].append(codigo)
                # Se tiver marcador de idade, adiciona em bpa_c_idade
                if 'idade' in proc.get('descricao', '').lower():
                    if codigo not in config['bpa_c_idade']:
                        config['bpa_c_idade'].append(codigo)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Config gerado: {filename}")
        print(f"   - BPA-C Geral: {len(config['bpa_c_geral'])} procedimentos")
        print(f"   - BPA-C Idade: {len(config['bpa_c_idade'])} procedimentos")


async def main():
    scraper = PowerBIScraperBPA()
    
    print("🤖 Iniciando extração do PowerBI...")
    print("📌 URL:", scraper.url)
    print()
    
    # Extrai dados (headless=False para ver o navegador)
    procedimentos = await scraper.extrair_procedimentos(headless=False)
    
    if procedimentos:
        print(f"\n✅ Extração concluída: {len(procedimentos)} procedimentos")
        
        # Mostra alguns exemplos
        print("\n📋 Primeiros 5 procedimentos:")
        for proc in procedimentos[:5]:
            print(f"   - {proc.get('codigo')}: {proc.get('descricao')}")
        
        # Salva em diferentes formatos
        scraper.salvar_json()
        scraper.salvar_csv()
        scraper.gerar_json_config()
    else:
        print("\n❌ Nenhum procedimento extraído")
        print("💡 Dica: Você pode aplicar os filtros manualmente e pressionar Enter")


if __name__ == "__main__":
    asyncio.run(main())
