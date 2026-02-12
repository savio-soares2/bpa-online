from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Paciente, Profissional

User = get_user_model()


class UserResponseSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "nome",
            "cbo",
            "cnes",
            "nome_unidade",
            "perfil",
            "ativo",
            "is_admin",
        )

    def get_is_admin(self, obj) -> bool:
        return obj.perfil == "admin"


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    senha = serializers.CharField(required=False, write_only=True)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    senha = serializers.CharField(required=False, write_only=True)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    nome = serializers.CharField(required=True)
    cbo = serializers.CharField(required=False, allow_blank=True)
    cnes = serializers.CharField(required=False, allow_blank=True)
    nome_unidade = serializers.CharField(required=False, allow_blank=True)


class ProfissionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profissional
        fields = (
            "id",
            "cnes",
            "cns",
            "cpf",
            "nome",
            "cbo",
            "ine",
            "vinculo",
        )


class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = (
            "id",
            "cns",
            "cpf",
            "nome",
            "data_nascimento",
            "sexo",
            "raca_cor",
            "nacionalidade",
            "municipio_ibge",
            "cep",
            "logradouro_codigo",
            "endereco",
            "numero",
            "complemento",
            "bairro",
            "telefone",
            "email",
        )
