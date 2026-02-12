#!/usr/bin/env python
"""
Script para criar usuário admin no sistema BPA Online.
"""
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.models import User


def create_admin_user(email: str = "admin@bpa.local", password: str = "admin123"):
    """Cria ou atualiza usuário admin."""
    
    # Extrair username do email
    username = email.split("@")[0]
    
    try:
        user = User.objects.get(username=username)
        print(f"Usuário '{username}' já existe. Atualizando senha...")
        user.set_password(password)
        user.perfil = "admin"
        user.ativo = True
        user.save()
        print(f"Senha atualizada com sucesso!")
    except User.DoesNotExist:
        print(f"Criando novo usuário admin '{username}'...")
        user = User.objects.create_user(
            username=username,
            password=password,
            nome="Administrador",
            email=email,
            perfil="admin",
            ativo=True
        )
        print(f"Usuário admin criado com sucesso!")
    
    print(f"\n=== Dados do usuário ===")
    print(f"Username: {user.username}")
    print(f"Nome: {user.nome}")
    print(f"Email: {user.email}")
    print(f"Perfil: {user.perfil}")
    print(f"Ativo: {user.ativo}")
    print(f"ID: {user.id}")
    
    return user


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Criar usuário admin")
    parser.add_argument("--email", default="admin@bpa.local", help="Email do admin")
    parser.add_argument("--password", default="admin123", help="Senha do admin")
    
    args = parser.parse_args()
    create_admin_user(args.email, args.password)
