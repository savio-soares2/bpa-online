#!/usr/bin/env python
"""Verifica usuário admin no banco"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_django.settings')

import django
django.setup()

from api.models import User

print("\n=== USUÁRIOS NO BANCO ===")
for u in User.objects.all():
    print(f"\nEmail: {u.email}")
    print(f"Nome: {u.nome}")
    print(f"Perfil: {u.perfil}")
    print(f"Ativo: {u.is_active}")
    print(f"Hash: {u.password[:60]}..." if u.password else "Hash: (vazio)")
    
    # Testar senha
    import bcrypt
    try:
        result = bcrypt.checkpw('admin123'.encode('utf-8'), u.password.encode('utf-8'))
        print(f"Senha 'admin123' válida: {result}")
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
