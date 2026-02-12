"""
Script de Validação de Consistência - BPA Online

Este script verifica a integridade dos dados e valores antes de gerar relatórios.
Execute sempre antes de enviar produção para garantir consistência financeira.

Uso:
    python validar_consistencia.py --cnes 6061478 --competencia 202511
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict

# Adiciona path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dbfread import DBF


class ValidadorBPA:
    """Validador de consistência do BPA"""
    
    def __init__(self, dbf_path: str):
        self.dbf_path = dbf_path
        self.erros = []
        self.avisos = []
        self.info = []
        
    def log_erro(self, msg: str):
        self.erros.append(f"❌ ERRO: {msg}")
        
    def log_aviso(self, msg: str):
        self.avisos.append(f"⚠️ AVISO: {msg}")
        
    def log_info(self, msg: str):
        self.info.append(f"ℹ️ INFO: {msg}")
        
    def log_ok(self, msg: str):
        self.info.append(f"✅ OK: {msg}")
    
    def validar_dbfs(self) -> bool:
        """Valida existência e integridade dos DBFs"""
        print("\n" + "="*60)
        print("1. VALIDAÇÃO DOS ARQUIVOS DBF")
        print("="*60)
        
        dbfs_necessarios = [
            ('S_PA.DBF', 'Procedimentos e valores'),
            ('S_CID.DBF', 'Classificação CID'),
            ('S_PACBO.DBF', 'Procedimento × CBO'),
            ('CADMUN.DBF', 'Municípios IBGE'),
        ]
        
        todos_ok = True
        for dbf_name, descricao in dbfs_necessarios:
            path = os.path.join(self.dbf_path, dbf_name)
            if os.path.exists(path):
                # Verifica data de modificação
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                size = os.path.getsize(path) / 1024  # KB
                
                self.log_ok(f"{dbf_name} encontrado ({size:.1f} KB, modificado em {mtime.strftime('%d/%m/%Y')})")
                
                # Verifica se consegue ler
                try:
                    table = DBF(path, encoding='latin-1')
                    count = sum(1 for _ in table)
                    self.log_info(f"  └─ {count} registros")
                except Exception as e:
                    self.log_erro(f"Não foi possível ler {dbf_name}: {e}")
                    todos_ok = False
            else:
                self.log_erro(f"{dbf_name} NÃO ENCONTRADO - {descricao}")
                todos_ok = False
                
        return todos_ok
    
    def validar_valores_sigtap(self, competencia: str) -> Dict:
        """Valida valores do SIGTAP para a competência"""
        print("\n" + "="*60)
        print("2. VALIDAÇÃO DOS VALORES SIGTAP")
        print("="*60)
        
        path = os.path.join(self.dbf_path, 'S_PA.DBF')
        table = DBF(path, encoding='latin-1')
        
        stats = {
            'total': 0,
            'com_valor': 0,
            'sem_valor': 0,
            'valor_total': 0.0,
            'maior_valor': 0.0,
            'proc_maior': '',
            'por_faixa': defaultdict(int)
        }
        
        for rec in table:
            stats['total'] += 1
            valor = rec.get('PA_TOTAL', 0) or 0
            
            if valor > 0:
                stats['com_valor'] += 1
                stats['valor_total'] += valor
                
                if valor > stats['maior_valor']:
                    stats['maior_valor'] = valor
                    stats['proc_maior'] = rec.get('PA_ID', '')
            else:
                stats['sem_valor'] += 1
            
            # Classificar por faixa de valor
            if valor == 0:
                stats['por_faixa']['R$ 0,00'] += 1
            elif valor <= 1:
                stats['por_faixa']['R$ 0,01 - 1,00'] += 1
            elif valor <= 10:
                stats['por_faixa']['R$ 1,01 - 10,00'] += 1
            elif valor <= 100:
                stats['por_faixa']['R$ 10,01 - 100,00'] += 1
            else:
                stats['por_faixa']['R$ 100,01+'] += 1
        
        self.log_ok(f"Total de procedimentos no SIGTAP: {stats['total']}")
        self.log_info(f"  └─ Com valor: {stats['com_valor']}")
        self.log_info(f"  └─ Sem valor (R$ 0,00): {stats['sem_valor']}")
        self.log_info(f"  └─ Maior valor: R$ {stats['maior_valor']:.2f} ({stats['proc_maior']})")
        
        print("\n  Distribuição por faixa de valor:")
        for faixa, count in sorted(stats['por_faixa'].items()):
            print(f"    {faixa}: {count} procedimentos")
        
        return stats
    
    def validar_firebird(self, cnes: str, competencia: str) -> Dict:
        """Valida dados no Firebird"""
        print("\n" + "="*60)
        print("3. VALIDAÇÃO DOS DADOS NO FIREBIRD")
        print("="*60)
        
        try:
            import firebirdsql
            
            conn = firebirdsql.connect(
                host='localhost',
                port=3050,
                database=r'C:\BPA\BPAMAG.GDB',
                user='SYSDBA',
                password='masterkey',
                charset='UTF8'
            )
            cursor = conn.cursor()
            
            # Total de registros
            cursor.execute("""
                SELECT COUNT(*) FROM S_PRD 
                WHERE PRD_UID = ? AND PRD_CMP = ?
            """, (cnes, competencia))
            total = cursor.fetchone()[0]
            
            # Por tipo (BPI/BPC)
            cursor.execute("""
                SELECT PRD_ORG, COUNT(*) FROM S_PRD 
                WHERE PRD_UID = ? AND PRD_CMP = ?
                GROUP BY PRD_ORG
            """, (cnes, competencia))
            por_tipo = dict(cursor.fetchall())
            
            # Profissionais únicos
            cursor.execute("""
                SELECT COUNT(DISTINCT PRD_CNSMED) FROM S_PRD 
                WHERE PRD_UID = ? AND PRD_CMP = ? AND PRD_ORG = 'BPI'
            """, (cnes, competencia))
            profissionais = cursor.fetchone()[0]
            
            # Registros com erro
            cursor.execute("""
                SELECT COUNT(*) FROM S_PRD 
                WHERE PRD_UID = ? AND PRD_CMP = ?
                AND (PRD_FLPA <> '0' OR PRD_FLCBO <> '0' OR PRD_FLCID <> '0')
            """, (cnes, competencia))
            com_erro = cursor.fetchone()[0]
            
            # Procedimentos distintos
            cursor.execute("""
                SELECT COUNT(DISTINCT PRD_PA) FROM S_PRD 
                WHERE PRD_UID = ? AND PRD_CMP = ? AND PRD_ORG = 'BPI'
            """, (cnes, competencia))
            procs_distintos = cursor.fetchone()[0]
            
            conn.close()
            
            self.log_ok(f"Conexão com Firebird OK")
            self.log_info(f"  └─ Total de registros: {total}")
            self.log_info(f"  └─ BPA Individualizado (BPI): {por_tipo.get('BPI', 0)}")
            self.log_info(f"  └─ BPA Consolidado (BPC): {por_tipo.get('BPC', 0)}")
            self.log_info(f"  └─ Profissionais distintos: {profissionais}")
            self.log_info(f"  └─ Procedimentos distintos: {procs_distintos}")
            
            if com_erro > 0:
                self.log_aviso(f"{com_erro} registros com flags de erro")
            else:
                self.log_ok("Nenhum registro com flag de erro")
            
            return {
                'total': total,
                'bpi': por_tipo.get('BPI', 0),
                'bpc': por_tipo.get('BPC', 0),
                'profissionais': profissionais,
                'procedimentos': procs_distintos,
                'com_erro': com_erro
            }
            
        except Exception as e:
            self.log_erro(f"Falha ao conectar no Firebird: {e}")
            return {}
    
    def calcular_valor_esperado(self, cnes: str, competencia: str) -> float:
        """Calcula valor total esperado"""
        print("\n" + "="*60)
        print("4. CÁLCULO DO VALOR FINANCEIRO")
        print("="*60)
        
        try:
            import firebirdsql
            
            # Carrega valores do DBF
            path = os.path.join(self.dbf_path, 'S_PA.DBF')
            table = DBF(path, encoding='latin-1')
            valores = {}
            for rec in table:
                pa_id = rec.get('PA_ID', '')
                valores[pa_id] = rec.get('PA_TOTAL', 0) or 0
            
            # Busca registros do Firebird
            conn = firebirdsql.connect(
                host='localhost',
                port=3050,
                database=r'C:\BPA\BPAMAG.GDB',
                user='SYSDBA',
                password='masterkey',
                charset='UTF8'
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT PRD_PA, PRD_QT_P FROM S_PRD 
                WHERE PRD_UID = ? AND PRD_CMP = ? AND PRD_ORG = 'BPI'
            """, (cnes, competencia))
            
            valor_total = 0.0
            registros = 0
            nao_encontrados = set()
            
            for row in cursor.fetchall():
                pa_cod = row[0] or ''
                qtd = row[1] or 0
                
                # Extrai PA_ID (9 primeiros dígitos)
                pa_id = pa_cod.replace('.', '').replace('-', '')[:9]
                
                if pa_id in valores:
                    valor_total += valores[pa_id] * int(qtd)
                else:
                    nao_encontrados.add(pa_id)
                
                registros += 1
            
            conn.close()
            
            self.log_ok(f"Valor total calculado: R$ {valor_total:,.2f}")
            self.log_info(f"  └─ Registros processados: {registros}")
            
            if nao_encontrados:
                self.log_aviso(f"{len(nao_encontrados)} procedimentos não encontrados no SIGTAP")
                for proc in list(nao_encontrados)[:5]:
                    print(f"    - {proc}")
                if len(nao_encontrados) > 5:
                    print(f"    ... e mais {len(nao_encontrados)-5}")
            
            return valor_total
            
        except Exception as e:
            self.log_erro(f"Falha ao calcular valor: {e}")
            return 0.0
    
    def gerar_relatorio(self, cnes: str, competencia: str):
        """Gera relatório completo de validação"""
        print("\n" + "="*60)
        print("RELATÓRIO DE VALIDAÇÃO - BPA ONLINE")
        print("="*60)
        print(f"CNES: {cnes}")
        print(f"Competência: {competencia}")
        print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Executa validações
        dbfs_ok = self.validar_dbfs()
        sigtap_stats = self.validar_valores_sigtap(competencia)
        firebird_stats = self.validar_firebird(cnes, competencia)
        valor_total = self.calcular_valor_esperado(cnes, competencia)
        
        # Resumo
        print("\n" + "="*60)
        print("RESUMO DA VALIDAÇÃO")
        print("="*60)
        
        print("\nERROS:")
        if self.erros:
            for e in self.erros:
                print(f"  {e}")
        else:
            print("  Nenhum erro encontrado ✅")
        
        print("\nAVISOS:")
        if self.avisos:
            for a in self.avisos:
                print(f"  {a}")
        else:
            print("  Nenhum aviso")
        
        print("\n" + "="*60)
        if not self.erros:
            print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO")
            print(f"   Valor esperado do BPA-I: R$ {valor_total:,.2f}")
        else:
            print("❌ VALIDAÇÃO CONCLUÍDA COM ERROS")
            print("   Corrija os erros antes de gerar o relatório!")
        print("="*60)
        
        return len(self.erros) == 0


def main():
    parser = argparse.ArgumentParser(description='Validador de Consistência BPA')
    parser.add_argument('--cnes', required=True, help='Código CNES')
    parser.add_argument('--competencia', required=True, help='Competência (YYYYMM)')
    parser.add_argument('--dbf-path', default=r'BPA-main\RELATORIOS', help='Caminho dos DBFs')
    
    args = parser.parse_args()
    
    validador = ValidadorBPA(args.dbf_path)
    sucesso = validador.gerar_relatorio(args.cnes, args.competencia)
    
    sys.exit(0 if sucesso else 1)


if __name__ == '__main__':
    main()
