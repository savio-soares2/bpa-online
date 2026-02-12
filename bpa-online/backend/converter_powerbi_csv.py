"""
Converte CSV exportado do PowerBI para o formato do sistema
"""
import pandas as pd
import json
import sys
from datetime import datetime

def converter_csv_powerbi(arquivo_csv, arquivo_saida='procedimentos_bpa_c_powerbi.json'):
    """
    Converte CSV do PowerBI para JSON do sistema
    
    Args:
        arquivo_csv: Arquivo CSV exportado do PowerBI
        arquivo_saida: Nome do arquivo JSON de saída
    """
    print(f"📂 Lendo arquivo: {arquivo_csv}")
    
    try:
        # Tenta diferentes encodings
        try:
            df = pd.read_csv(arquivo_csv, encoding='utf-8')
        except:
            try:
                df = pd.read_csv(arquivo_csv, encoding='latin-1')
            except:
                df = pd.read_csv(arquivo_csv, encoding='utf-8-sig')
        
        print(f"✅ Arquivo lido: {len(df)} linhas")
        print(f"📋 Colunas: {list(df.columns)}")
        
        # Mostra primeiras linhas
        print("\n📊 Primeiras 5 linhas:")
        print(df.head())
        
        # Detecta colunas
        col_codigo = None
        col_descricao = None
        col_tipo = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'codigo' in col_lower or 'procedimento' in col_lower or 'cod' in col_lower:
                col_codigo = col
            elif 'descricao' in col_lower or 'nome' in col_lower or 'desc' in col_lower:
                col_descricao = col
            elif 'tipo' in col_lower or 'instrumento' in col_lower:
                col_tipo = col
        
        if not col_codigo:
            print("\n⚠️ Coluna de código não detectada automaticamente")
            print("Colunas disponíveis:", list(df.columns))
            col_codigo = input("Digite o nome da coluna de código: ")
        
        print(f"\n✅ Usando colunas:")
        print(f"   - Código: {col_codigo}")
        if col_descricao:
            print(f"   - Descrição: {col_descricao}")
        if col_tipo:
            print(f"   - Tipo: {col_tipo}")
        
        # Processa dados
        config = {
            "bpa_c_geral": [],
            "bpa_c_idade": [],
            "fonte": f"PowerBI - Convertido de {arquivo_csv}",
            "data_extracao": datetime.now().isoformat(),
            "total_procedimentos": 0,
            "detalhes": []
        }
        
        for idx, row in df.iterrows():
            try:
                codigo = str(row[col_codigo]).strip()
                
                # Remove caracteres não numéricos
                codigo = ''.join(filter(str.isdigit, codigo))
                
                if not codigo or len(codigo) != 10:
                    continue
                
                # Detecta tipo
                tipo = 'bpa_c'  # Padrão
                descricao = str(row[col_descricao]) if col_descricao else ''
                
                if col_tipo:
                    tipo_valor = str(row[col_tipo]).lower()
                    if 'consolidado' in tipo_valor:
                        tipo = 'bpa_c'
                    elif 'individualizado' in tipo_valor:
                        tipo = 'bpa_i'
                
                # Adiciona na categoria apropriada
                if tipo == 'bpa_c':
                    if codigo not in config['bpa_c_geral']:
                        config['bpa_c_geral'].append(codigo)
                    
                    # Verifica se é por idade
                    if 'idade' in descricao.lower() or 'faixa etaria' in descricao.lower():
                        if codigo not in config['bpa_c_idade']:
                            config['bpa_c_idade'].append(codigo)
                
                # Guarda detalhes para debug
                config['detalhes'].append({
                    'codigo': codigo,
                    'descricao': descricao,
                    'tipo': tipo
                })
                
            except Exception as e:
                print(f"⚠️ Erro na linha {idx}: {e}")
        
        config['total_procedimentos'] = len(config['bpa_c_geral']) + len(config['bpa_c_idade'])
        
        # Salva JSON
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Conversão concluída!")
        print(f"💾 Arquivo salvo: {arquivo_saida}")
        print(f"\n📊 Estatísticas:")
        print(f"   - Total de procedimentos: {config['total_procedimentos']}")
        print(f"   - BPA-C Geral: {len(config['bpa_c_geral'])}")
        print(f"   - BPA-C com Idade: {len(config['bpa_c_idade'])}")
        
        print(f"\n📋 Primeiros 10 códigos BPA-C:")
        for codigo in config['bpa_c_geral'][:10]:
            detalhe = next((d for d in config['detalhes'] if d['codigo'] == codigo), None)
            desc = detalhe['descricao'][:60] if detalhe else ''
            print(f"   - {codigo}: {desc}")
        
        print(f"\n💡 Próximo passo:")
        print(f"   Copie o arquivo para: backend/data/procedimentos_bpa_c.json")
        print(f"   Comando: copy {arquivo_saida} backend\\data\\procedimentos_bpa_c.json")
        
        return config
        
    except Exception as e:
        print(f"\n❌ Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python converter_powerbi_csv.py <arquivo.csv>")
        print("\nExemplo:")
        print("   python converter_powerbi_csv.py procedimentos_exportados.csv")
        sys.exit(1)
    
    arquivo_csv = sys.argv[1]
    arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else 'procedimentos_bpa_c_powerbi.json'
    
    converter_csv_powerbi(arquivo_csv, arquivo_saida)
