#!/usr/bin/env python
"""
Script para testar autenticação do usuário admin.
"""
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth import authenticate
from api.models import User


def test_auth():
    """Testa autenticação do usuário admin."""
    print("=== Teste de Autenticação ===\n")
    
    # Test 1: Verificar usuário existe
    print("1. Verificando se usuário 'admin' existe...")
    try:
        user = User.objects.get(username="admin")
        print(f"   ✓ Usuário encontrado: {user.username} (ID: {user.id})")
        print(f"   - Nome: {user.nome}")
        print(f"   - Email: {user.email}")
        print(f"   - Perfil: {user.perfil}")
        print(f"   - Ativo: {user.ativo}")
        print(f"   - CBO: {user.cbo}")  # Should be None
    except User.DoesNotExist:
        print("   ✗ Usuário não encontrado!")
        return
    
    # Test 2: Verificar senha
    print("\n2. Testando autenticação com senha 'admin123'...")
    authenticated_user = authenticate(username="admin", password="admin123")
    if authenticated_user:
        print(f"   ✓ Autenticação bem sucedida!")
        print(f"   - is_active: {authenticated_user.is_active}")
        print(f"   - is_staff: {authenticated_user.is_staff}")
        print(f"   - is_superuser: {authenticated_user.is_superuser}")
    else:
        print("   ✗ Autenticação falhou!")
        
        # Debug: verificar se a senha está corretamente hasheada
        print("\n   Debug: Verificando hash da senha...")
        if user.check_password("admin123"):
            print("   - check_password('admin123') retornou True")
        else:
            print("   - check_password('admin123') retornou False")
            print(f"   - Hash atual: {user.password[:50]}...")
    
    # Test 3: Testar JWT
    print("\n3. Testando geração de token JWT...")
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        print(f"   ✓ Token gerado com sucesso!")
        print(f"   - Access Token: {str(refresh.access_token)[:50]}...")
        print(f"   - Refresh Token: {str(refresh)[:50]}...")
    except Exception as e:
        print(f"   ✗ Erro ao gerar token: {e}")
    
    print("\n=== Teste Concluído ===")


if __name__ == "__main__":
    test_auth()
