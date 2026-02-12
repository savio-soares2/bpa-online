#!/usr/bin/env python
"""
Script para adicionar coluna last_login à tabela usuarios.
Necessário para compatibilidade com Django AbstractBaseUser.
"""
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection


def add_last_login_column():
    """Adiciona coluna last_login se não existir."""
    with connection.cursor() as cursor:
        # Verificar se coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'usuarios' 
            AND column_name = 'last_login';
        """)
        
        if cursor.fetchone():
            print("Coluna 'last_login' já existe na tabela 'usuarios'.")
            return False
        
        # Adicionar coluna
        print("Adicionando coluna 'last_login' à tabela 'usuarios'...")
        cursor.execute("""
            ALTER TABLE usuarios 
            ADD COLUMN last_login TIMESTAMP WITHOUT TIME ZONE NULL;
        """)
        print("Coluna 'last_login' adicionada com sucesso!")
        return True


if __name__ == "__main__":
    add_last_login_column()
