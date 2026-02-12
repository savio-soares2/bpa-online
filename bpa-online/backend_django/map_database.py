#!/usr/bin/env python
"""
Script para mapear o schema do banco de dados PostgreSQL
e gerar documentação das tabelas e colunas.
"""
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection
from datetime import datetime


def get_all_tables():
    """Retorna lista de todas as tabelas no schema public."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        return [row[0] for row in cursor.fetchall()]


def get_table_columns(table_name):
    """Retorna informações das colunas de uma tabela."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s
            ORDER BY ordinal_position;
        """, [table_name])
        return cursor.fetchall()


def get_table_constraints(table_name):
    """Retorna constraints da tabela (PK, FK, UNIQUE)."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            LEFT JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = 'public'
            AND tc.table_name = %s
            ORDER BY tc.constraint_type, tc.constraint_name;
        """, [table_name])
        return cursor.fetchall()


def get_table_indexes(table_name):
    """Retorna índices da tabela."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = %s
            ORDER BY indexname;
        """, [table_name])
        return cursor.fetchall()


def get_table_row_count(table_name):
    """Retorna contagem aproximada de linhas."""
    with connection.cursor() as cursor:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            return cursor.fetchone()[0]
        except Exception:
            return "N/A"


def generate_mapping():
    """Gera o mapeamento completo do banco."""
    output = []
    output.append("# Mapeamento do Banco de Dados PostgreSQL - BPA Online")
    output.append(f"# Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    output.append("")
    
    tables = get_all_tables()
    output.append(f"## Total de Tabelas: {len(tables)}")
    output.append("")
    
    # Summary
    output.append("## Sumário das Tabelas")
    output.append("-" * 40)
    for table in tables:
        count = get_table_row_count(table)
        output.append(f"  - {table} ({count} registros)")
    output.append("")
    
    # Detailed mapping
    output.append("=" * 80)
    output.append("## Detalhamento por Tabela")
    output.append("=" * 80)
    output.append("")
    
    for table in tables:
        output.append(f"### Tabela: {table}")
        output.append("-" * 60)
        
        # Columns
        columns = get_table_columns(table)
        output.append("")
        output.append("#### Colunas:")
        output.append(f"{'Nome':<30} {'Tipo':<20} {'Nullable':<10} {'Default':<30}")
        output.append("-" * 90)
        
        for col in columns:
            col_name, data_type, nullable, default, max_len, num_prec, num_scale = col
            
            # Format data type
            if max_len:
                data_type = f"{data_type}({max_len})"
            elif num_prec and data_type == 'numeric':
                data_type = f"numeric({num_prec},{num_scale or 0})"
            
            nullable_str = "YES" if nullable == "YES" else "NO"
            default_str = str(default)[:28] if default else ""
            
            output.append(f"{col_name:<30} {data_type:<20} {nullable_str:<10} {default_str:<30}")
        
        # Constraints
        constraints = get_table_constraints(table)
        if constraints:
            output.append("")
            output.append("#### Constraints:")
            for const in constraints:
                const_name, const_type, col_name, fk_table, fk_col = const
                if const_type == "FOREIGN KEY" and fk_table:
                    output.append(f"  - {const_type}: {col_name} -> {fk_table}.{fk_col}")
                elif col_name:
                    output.append(f"  - {const_type}: {col_name}")
        
        # Indexes
        indexes = get_table_indexes(table)
        if indexes:
            output.append("")
            output.append("#### Índices:")
            for idx in indexes:
                idx_name, idx_def = idx
                output.append(f"  - {idx_name}")
        
        output.append("")
        output.append("")
    
    return "\n".join(output)


def generate_django_model_suggestions():
    """Gera sugestões de models Django baseado no schema."""
    output = []
    output.append("")
    output.append("=" * 80)
    output.append("## Sugestões de Models Django")
    output.append("=" * 80)
    output.append("")
    
    tables = get_all_tables()
    
    # Type mapping
    type_map = {
        'integer': 'IntegerField',
        'bigint': 'BigIntegerField',
        'smallint': 'SmallIntegerField',
        'character varying': 'CharField',
        'varchar': 'CharField',
        'text': 'TextField',
        'boolean': 'BooleanField',
        'timestamp without time zone': 'DateTimeField',
        'timestamp with time zone': 'DateTimeField',
        'date': 'DateField',
        'time without time zone': 'TimeField',
        'numeric': 'DecimalField',
        'double precision': 'FloatField',
        'real': 'FloatField',
        'json': 'JSONField',
        'jsonb': 'JSONField',
        'uuid': 'UUIDField',
    }
    
    for table in tables:
        # Skip Django internal tables
        if table.startswith('django_') or table.startswith('auth_'):
            continue
            
        columns = get_table_columns(table)
        constraints = get_table_constraints(table)
        
        # Find primary key
        pk_col = None
        for const in constraints:
            if const[1] == "PRIMARY KEY":
                pk_col = const[2]
                break
        
        # Generate model class
        class_name = ''.join(word.capitalize() for word in table.split('_'))
        
        output.append(f"class {class_name}(models.Model):")
        output.append(f'    """Model para tabela {table}."""')
        output.append("")
        
        for col in columns:
            col_name, data_type, nullable, default, max_len, num_prec, num_scale = col
            
            # Map field type
            field_type = type_map.get(data_type, 'CharField')
            
            # Build field arguments
            args = []
            
            if col_name == pk_col:
                if data_type in ('integer', 'bigint'):
                    field_type = 'AutoField' if data_type == 'integer' else 'BigAutoField'
                    args.append('primary_key=True')
            
            if max_len and field_type == 'CharField':
                args.append(f'max_length={max_len}')
            
            if num_prec and field_type == 'DecimalField':
                args.append(f'max_digits={num_prec}')
                args.append(f'decimal_places={num_scale or 0}')
            
            if nullable == "YES" and col_name != pk_col:
                args.append('null=True')
                args.append('blank=True')
            
            args_str = ', '.join(args)
            output.append(f"    {col_name} = models.{field_type}({args_str})")
        
        output.append("")
        output.append("    class Meta:")
        output.append(f"        db_table = '{table}'")
        output.append("        managed = False")
        output.append("")
        output.append("")
    
    return "\n".join(output)


if __name__ == "__main__":
    print("Mapeando banco de dados...")
    
    # Generate mapping
    mapping = generate_mapping()
    suggestions = generate_django_model_suggestions()
    
    full_output = mapping + suggestions
    
    # Print to console
    print(full_output)
    
    # Save to file
    output_file = os.path.join(os.path.dirname(__file__), '..', 'DATABASE_MAPPING.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_output)
    
    print(f"\n\nMapeamento salvo em: {output_file}")
