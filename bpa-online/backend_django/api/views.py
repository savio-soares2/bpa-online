import hashlib
import os
from pathlib import Path

import bcrypt
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError
from django.db import connection
from django.http import FileResponse
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .authentication import encode_token
from .legacy import get_bpa_database, get_dbf_manager
from .permissions import IsAdminPerfil
from .models import Paciente, Profissional
from .serializers import (
	LoginSerializer,
	PacienteSerializer,
	ProfissionalSerializer,
	RegisterSerializer,
	UserResponseSerializer,
)

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
	return Response({"status": "ok"})


def _verify_legacy_password(raw_password: str, stored_hash: str) -> bool:
	if stored_hash.startswith("$2a$") or stored_hash.startswith("$2b$"):
		return bcrypt.checkpw(raw_password.encode("utf-8"), stored_hash.encode("utf-8"))
	if ":" in stored_hash:
		try:
			salt, hash_value = stored_hash.split(":", 1)
			hash_obj = hashlib.pbkdf2_hmac(
				"sha256",
				raw_password.encode("utf-8"),
				salt.encode("utf-8"),
				100000,
			)
			return hash_obj.hex() == hash_value
		except ValueError:
			return False
	return False


def _verify_password(user, raw_password: str) -> bool:
	try:
		if check_password(raw_password, user.password):
			return True
	except ValueError:
		pass

	if _verify_legacy_password(raw_password, user.password):
		user.set_password(raw_password)
		user.save(update_fields=["password"])
		return True
	return False


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
	serializer = LoginSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	data = serializer.validated_data

	email = data.get("email")
	senha = data.get("senha")
	username = data.get("username")
	password = data.get("password")

	identifier = email or username
	secret = senha or password
	if not identifier or not secret:
		return Response(
			{"detail": "Credenciais invalidas"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	User = get_user_model()
	if email:
		user = User.objects.filter(email=email).first()
	else:
		user = User.objects.filter(username=username).first()

	if not user or not user.is_active:
		return Response(
			{"detail": "Credenciais invalidas"},
			status=status.HTTP_401_UNAUTHORIZED,
		)

	if not _verify_password(user, secret):
		return Response(
			{"detail": "Credenciais invalidas"},
			status=status.HTTP_401_UNAUTHORIZED,
		)

	token = encode_token(
		{
			"user_id": user.id,
			"email": user.email,
			"cnes": user.cnes,
			"is_admin": user.perfil == "admin",
		}
	)

	return Response(
		{
			"access_token": token,
			"token_type": "bearer",
			"user": UserResponseSerializer(user).data,
		}
	)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
	serializer = RegisterSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	data = serializer.validated_data

	email = data.get("email")
	senha = data.get("senha")
	username = data.get("username")
	password = data.get("password")
	nome = data["nome"]

	if not (email or username):
		return Response(
			{"detail": "Email ou username obrigatorio"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	raw_password = senha or password
	if not raw_password:
		return Response(
			{"detail": "Senha obrigatoria"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	if not username:
		username = email

	User = get_user_model()
	try:
		user = User.objects.create_user(
			username=username,
			password=raw_password,
			email=email,
			nome=nome,
			cbo=data.get("cbo") or "",
			cnes=data.get("cnes") or "",
			nome_unidade=data.get("nome_unidade") or "",
			perfil="digitador",
			ativo=True,
		)
	except IntegrityError:
		return Response(
			{"detail": "Usuario ja cadastrado"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	token = encode_token(
		{
			"user_id": user.id,
			"email": user.email,
			"cnes": user.cnes,
			"is_admin": user.perfil == "admin",
		}
	)

	return Response(
		{
			"access_token": token,
			"token_type": "bearer",
			"user": UserResponseSerializer(user).data,
		},
		status=status.HTTP_201_CREATED,
	)


@api_view(["GET"])
def get_me(request):
	return Response(UserResponseSerializer(request.user).data)


@api_view(["GET", "POST"])
@permission_classes([IsAdminPerfil])
def admin_users(request):
	User = get_user_model()
	if request.method == "GET":
		users = User.objects.all().order_by("id")
		return Response(UserResponseSerializer(users, many=True).data)

	data = request.data
	email = data.get("email")
	username = data.get("username") or email
	senha = data.get("senha")
	nome = data.get("nome")
	if not (email and senha and nome):
		return Response(
			{"detail": "email, senha e nome sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	try:
		user = User.objects.create_user(
			username=username,
			password=senha,
			email=email,
			nome=nome,
			cbo=data.get("cbo") or "",
			cnes=data.get("cnes") or "",
			nome_unidade=data.get("nome_unidade") or "",
			perfil=data.get("perfil") or "digitador",
			ativo=True,
		)
	except IntegrityError:
		return Response(
			{"detail": "Usuario ja cadastrado"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	return Response(UserResponseSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAdminPerfil])
def admin_user_detail(request, user_id: int):
	User = get_user_model()
	try:
		user = User.objects.get(id=user_id)
	except User.DoesNotExist:
		return Response({"detail": "Usuario nao encontrado"}, status=status.HTTP_404_NOT_FOUND)

	if request.method == "DELETE":
		user.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)

	for field in ["nome", "email", "cbo", "cnes", "nome_unidade", "perfil"]:
		if field in request.data:
			setattr(user, field, request.data.get(field))

	if "ativo" in request.data:
		user.ativo = bool(request.data.get("ativo"))

	user.save()
	return Response(UserResponseSerializer(user).data)


@api_view(["PUT"])
@permission_classes([IsAdminPerfil])
def admin_toggle_user(request, user_id: int):
	ativo = request.query_params.get("ativo")
	ativo_value = True if str(ativo).lower() in {"1", "true", "yes"} else False

	User = get_user_model()
	try:
		user = User.objects.get(id=user_id)
	except User.DoesNotExist:
		return Response({"detail": "Usuario nao encontrado"}, status=status.HTTP_404_NOT_FOUND)

	user.ativo = ativo_value
	user.save(update_fields=["ativo"])
	return Response({"message": "Usuario atualizado"})


@api_view(["POST"])
@permission_classes([IsAdminPerfil])
def admin_reset_password(request, user_id: int):
	nova_senha = request.data.get("nova_senha")
	if not nova_senha:
		return Response(
			{"detail": "nova_senha obrigatoria"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	User = get_user_model()
	try:
		user = User.objects.get(id=user_id)
	except User.DoesNotExist:
		return Response({"detail": "Usuario nao encontrado"}, status=status.HTTP_404_NOT_FOUND)

	user.set_password(nova_senha)
	user.save(update_fields=["password"])
	return Response({"message": "Senha atualizada"})


@api_view(["GET"])
@permission_classes([IsAdminPerfil])
def admin_list_cbos(request):
	query = request.query_params.get("q")
	limit = int(request.query_params.get("limit", "50"))

	dbf_manager = get_dbf_manager()
	if query:
		results = dbf_manager.search_cbos(query, limit=limit)
	else:
		results = dbf_manager.get_all_cbos()[:limit]

	return Response(results)


@api_view(["GET"])
@permission_classes([IsAdminPerfil])
def admin_database_overview(request):
	try:
		with connection.cursor() as cursor:
			cursor.execute(
				"""
				SELECT 
					prd_uid as cnes,
					prd_cmp as competencia,
					COUNT(*) as total_bpa_i,
					SUM(CASE WHEN prd_exportado = FALSE THEN 1 ELSE 0 END) as pendentes,
					SUM(CASE WHEN prd_exportado = TRUE THEN 1 ELSE 0 END) as exportados,
					MIN(created_at) as primeira_insercao,
					MAX(created_at) as ultima_insercao
				FROM bpa_individualizado
				GROUP BY prd_uid, prd_cmp
				ORDER BY prd_uid, prd_cmp DESC;
				"""
			)
			bpa_i_data = [
				{
					"cnes": row[0],
					"competencia": row[1],
					"total": row[2],
					"pendentes": row[3],
					"exportados": row[4],
					"primeira_insercao": row[5].isoformat() if row[5] else None,
					"ultima_insercao": row[6].isoformat() if row[6] else None,
					"tipo": "bpa_i",
				}
				for row in cursor.fetchall()
			]

			cursor.execute(
				"""
				SELECT 
					prd_uid as cnes,
					prd_cmp as competencia,
					COUNT(*) as total_bpa_c,
					SUM(CASE WHEN prd_exportado = FALSE THEN 1 ELSE 0 END) as pendentes,
					SUM(CASE WHEN prd_exportado = TRUE THEN 1 ELSE 0 END) as exportados,
					MIN(created_at) as primeira_insercao,
					MAX(created_at) as ultima_insercao
				FROM bpa_consolidado
				GROUP BY prd_uid, prd_cmp
				ORDER BY prd_uid, prd_cmp DESC;
				"""
			)
			bpa_c_data = [
				{
					"cnes": row[0],
					"competencia": row[1],
					"total": row[2],
					"pendentes": row[3],
					"exportados": row[4],
					"primeira_insercao": row[5].isoformat() if row[5] else None,
					"ultima_insercao": row[6].isoformat() if row[6] else None,
					"tipo": "bpa_c",
				}
				for row in cursor.fetchall()
			]

			cursor.execute(
				"""
				SELECT DISTINCT prd_uid 
				FROM bpa_individualizado
				UNION
				SELECT DISTINCT prd_uid 
				FROM bpa_consolidado
				ORDER BY prd_uid;
				"""
			)
			cnes_list = [row[0] for row in cursor.fetchall()]

			cursor.execute("SELECT COUNT(*) FROM bpa_individualizado;")
			total_bpa_i = cursor.fetchone()[0]

			cursor.execute("SELECT COUNT(*) FROM bpa_consolidado;")
			total_bpa_c = cursor.fetchone()[0]

			cursor.execute("SELECT COUNT(*) FROM profissionais;")
			total_prof = cursor.fetchone()[0]

			cursor.execute("SELECT COUNT(*) FROM pacientes;")
			total_pac = cursor.fetchone()[0]

		return Response(
			{
				"success": True,
				"cnes_list": cnes_list,
				"total_cnes": len(cnes_list),
				"bpa_i": bpa_i_data,
				"bpa_c": bpa_c_data,
				"totals": {
					"bpa_i": total_bpa_i,
					"bpa_c": total_bpa_c,
					"profissionais": total_prof,
					"pacientes": total_pac,
				},
			}
		)
	except Exception as exc:
		return Response(
			{"detail": str(exc)},
			status=status.HTTP_500_INTERNAL_SERVER_ERROR,
		)


@api_view(["GET"])
@permission_classes([IsAdminPerfil])
def admin_historico_extracoes(request):
	cnes = request.query_params.get("cnes")
	limit = int(request.query_params.get("limit", "20"))
	offset = int(request.query_params.get("offset", "0"))

	db = get_bpa_database()
	result = db.list_historico_extracoes(cnes=cnes, limit=limit, offset=offset)
	for record in result.get("records", []):
		if record.get("created_at"):
			record["created_at"] = record["created_at"].isoformat()

	return Response({"success": True, **result})


@api_view(["POST"])
@permission_classes([IsAdminPerfil])
def admin_fix_encoding(request):
	sigtap_parser = None
	sigtap_dir = os.getenv("SIGTAP_DIR", "/app/sigtap")
	if os.path.exists(sigtap_dir):
		try:
			from services.sigtap_parser import SigtapParser

			sigtap_parser = SigtapParser(sigtap_dir)
		except Exception:
			sigtap_parser = None

	db = get_bpa_database()
	result = db.fix_encoding_historico(sigtap_parser=sigtap_parser)

	msg = f"Encoding corrigido em {result.get('updated', 0)} registros"
	if result.get("had_sigtap"):
		msg += " (nomes atualizados do SIGTAP)"
	else:
		msg += " (SIGTAP nao disponivel, nomes genericos usados)"

	return Response({"success": True, "message": msg, **result})


@api_view(["DELETE"])
@permission_classes([IsAdminPerfil])
def admin_delete_data(request):
	cnes = request.query_params.get("cnes")
	competencia = request.query_params.get("competencia")
	tipo = request.query_params.get("tipo")

	if not cnes or not tipo:
		return Response(
			{"detail": "cnes e tipo sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	deleted_count = 0
	with connection.cursor() as cursor:
		if tipo in {"bpa_i", "all"}:
			if competencia:
				cursor.execute(
					"DELETE FROM bpa_individualizado WHERE prd_uid = %s AND prd_cmp = %s",
					[cnes, competencia],
				)
			else:
				cursor.execute(
					"DELETE FROM bpa_individualizado WHERE prd_uid = %s",
					[cnes],
				)
			deleted_count += cursor.rowcount

		if tipo in {"bpa_c", "all"}:
			if competencia:
				cursor.execute(
					"DELETE FROM bpa_consolidado WHERE prd_uid = %s AND prd_cmp = %s",
					[cnes, competencia],
				)
			else:
				cursor.execute(
					"DELETE FROM bpa_consolidado WHERE prd_uid = %s",
					[cnes],
				)
			deleted_count += cursor.rowcount

		if tipo in {"profissionais", "all"}:
			cursor.execute("DELETE FROM profissionais WHERE cnes = %s", [cnes])
			deleted_count += cursor.rowcount

		if tipo in {"pacientes", "all"}:
			cursor.execute(
				"""
				DELETE FROM pacientes
				WHERE cns NOT IN (
					SELECT DISTINCT prd_cnspac
					FROM bpa_individualizado
					WHERE prd_cnspac IS NOT NULL
				)
				"""
			)
			deleted_count += cursor.rowcount

	return Response(
		{
			"success": True,
			"deleted": deleted_count,
			"cnes": cnes,
			"competencia": competencia,
			"tipo": tipo,
			"message": f"Deletados {deleted_count} registros",
		}
	)


@api_view(["GET"])
def dashboard_stats(request):
	cnes_filter = request.query_params.get("cnes_filter")
	user = request.user

	cnes = cnes_filter or user.cnes
	nome_unidade = "" if cnes_filter else (user.nome_unidade or "")

	if not cnes:
		return Response(
			{
				"cnes": "",
				"nome_unidade": nome_unidade,
				"usuario": user.nome,
				"bpai": {"total": 0, "pendentes": 0, "exportados": 0, "competencias": []},
				"bpac": {"total": 0, "pendentes": 0, "exportados": 0, "competencias": []},
				"profissionais": 0,
				"pacientes": 0,
				"ultimas_exportacoes": [],
			}
		)

	db = get_bpa_database()
	stats = db.get_stats_by_cnes(cnes)

	return Response(
		{
			"cnes": cnes,
			"nome_unidade": nome_unidade or stats.get("nome_unidade", ""),
			"usuario": user.nome,
			"bpai": {
				"total": stats.get("bpai_total", 0),
				"pendentes": stats.get("bpai_pendente", 0),
				"exportados": stats.get("bpai_exportado", 0),
				"competencias": stats.get("bpai_competencias", []),
			},
			"bpac": {
				"total": stats.get("bpac_total", 0),
				"pendentes": stats.get("bpac_pendente", 0),
				"exportados": stats.get("bpac_exportado", 0),
				"competencias": stats.get("bpac_competencias", []),
			},
			"profissionais": stats.get("profissionais", 0),
			"pacientes": stats.get("pacientes", 0),
			"ultimas_exportacoes": stats.get("ultimas_exportacoes", []),
		}
	)


@api_view(["GET"])
def bpa_stats(request):
	cnes = request.query_params.get("cnes") or request.user.cnes
	competencia = request.query_params.get("competencia")
	if not cnes:
		return Response({"detail": "CNES obrigatorio"}, status=status.HTTP_400_BAD_REQUEST)

	db = get_bpa_database()
	stats = db.get_bpa_stats(cnes, competencia)
	return Response(stats)


@api_view(["GET", "POST"])
def profissionais(request):
	if request.method == "GET":
		cnes = request.query_params.get("cnes")
		queryset = Profissional.objects.all().order_by("nome")
		if cnes:
			queryset = queryset.filter(cnes=cnes)
		return Response(ProfissionalSerializer(queryset, many=True).data)

	serializer = ProfissionalSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	profissional = serializer.save()
	return Response(ProfissionalSerializer(profissional).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def profissional_detail(request, cns: str):
	profissional = Profissional.objects.filter(cns=cns).first()
	if not profissional:
		return Response(status=status.HTTP_404_NOT_FOUND)
	return Response(ProfissionalSerializer(profissional).data)


@api_view(["GET", "POST"])
@permission_classes([IsAdminPerfil])
def admin_profissionais(request):
	if request.method == "GET":
		cnes = request.query_params.get("cnes")
		queryset = Profissional.objects.all().order_by("nome")
		if cnes:
			queryset = queryset.filter(cnes=cnes)
		return Response(ProfissionalSerializer(queryset, many=True).data)

	serializer = ProfissionalSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	profissional = serializer.save()
	return Response(ProfissionalSerializer(profissional).data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAdminPerfil])
def admin_profissional_delete(request, profissional_id: int):
	profissional = Profissional.objects.filter(id=profissional_id).first()
	if not profissional:
		return Response(status=status.HTTP_404_NOT_FOUND)
	profissional.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def pacientes_search(request):
	termo = request.query_params.get("q", "").strip()
	if not termo:
		return Response([])

	queryset = Paciente.objects.filter(nome__icontains=termo) | Paciente.objects.filter(
		cns__icontains=termo
	)
	results = queryset.order_by("nome")[:50]
	return Response(PacienteSerializer(results, many=True).data)


@api_view(["POST"])
def pacientes_create(request):
	serializer = PacienteSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	paciente = serializer.save()
	return Response(PacienteSerializer(paciente).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def paciente_detail(request, cns: str):
	paciente = Paciente.objects.filter(cns=cns).first()
	if not paciente:
		return Response(status=status.HTTP_404_NOT_FOUND)
	return Response(PacienteSerializer(paciente).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def procedures_search(request):
	query = request.query_params.get("q", "").strip()
	limit = int(request.query_params.get("limit", "50"))
	my_only = request.query_params.get("my_only") in {"1", "true", "True"}

	dbf_manager = get_dbf_manager()
	procedimentos_info = dbf_manager.get_procedimentos_info()

	user = request.user if getattr(request.user, "is_authenticated", False) else None
	if my_only and user and user.cbo:
		allowed = set(dbf_manager.get_procedimentos_for_cbo(user.cbo))
	elif my_only:
		return Response([])
	else:
		allowed = None

	results = []
	for codigo, info in procedimentos_info.items():
		if allowed is not None and codigo not in allowed:
			continue
		if query and query.lower() not in codigo.lower() and query.lower() not in info.get("descricao", "").lower():
			continue
		valor = float(info.get("valor_sh", 0) or 0) + float(info.get("valor_sp", 0) or 0) + float(info.get("valor_sa", 0) or 0)
		results.append({"codigo": codigo, "descricao": info.get("descricao"), "valor": valor})
		if len(results) >= limit:
			break

	return Response(results)


@api_view(["GET"])
@permission_classes([AllowAny])
def procedimento_detail(request, codigo: str):
	from services.sigtap_filter_service import get_sigtap_filter_service
	
	sigtap = get_sigtap_filter_service()
	info = sigtap.get_procedimento_info(codigo)
	
	if not info:
		return Response(
			{"detail": f"Procedimento {codigo} não encontrado"},
			status=status.HTTP_404_NOT_FOUND
		)
	
	return Response({
		"codigo": info['codigo'],
		"nome": info['nome'],
		"descricao": info['nome'],  # Alias para compatibilidade
		"valor_sa": info['valor_sa'],
		"valor_sh": info['valor_sh'],
		"valor_sp": info['valor_sp'],
		"valor": info['valor_total'],
		"complexidade": info['complexidade'],
		"registros": info['registros'],
	})


@api_view(["GET"])
def bpa_inconsistencies(request):
	cnes = request.query_params.get("cnes")
	competencia = request.query_params.get("competencia")
	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.inconsistency_service import InconsistencyService

	service = InconsistencyService()
	report = service.get_inconsistency_report(cnes, competencia)
	return Response(report)


@api_view(["GET", "POST"])
def bpa_individualizado(request):
	if request.method == "GET":
		competencia = request.query_params.get("competencia")
		exportado = request.query_params.get("exportado")
		if not competencia:
			return Response(
				{"detail": "competencia obrigatoria"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		exportado_value = None
		if exportado is not None:
			exportado_value = str(exportado).lower() in {"1", "true", "yes"}

		db = get_bpa_database()
		records = db.list_bpa_individualizado(request.user.cnes, competencia, exportado_value)
		return Response(records)

	data = request.data
	bpa_data = {
		"prd_uid": request.user.cnes,
		"prd_cmp": data.get("competencia"),
		"prd_cnsmed": data.get("cns_profissional"),
		"prd_cbo": data.get("cbo"),
		"prd_ine": data.get("ine"),
		"prd_cnspac": data.get("cns_paciente"),
		"prd_nmpac": data.get("nome_paciente"),
		"prd_dtnasc": data.get("data_nascimento"),
		"prd_sexo": data.get("sexo"),
		"prd_raca": data.get("raca_cor"),
		"prd_ibge": data.get("municipio_ibge"),
		"prd_dtaten": data.get("data_atendimento"),
		"prd_pa": data.get("procedimento"),
		"prd_qt_p": data.get("quantidade"),
		"prd_cid": data.get("cid"),
	}

	db = get_bpa_database()
	db.save_profissional(
		{
			"cns": data.get("cns_profissional"),
			"cbo": data.get("cbo"),
			"cnes": request.user.cnes,
			"ine": data.get("ine"),
			"nome": data.get("nome_profissional", ""),
		}
	)

	record_id = db.save_bpa_individualizado(bpa_data)
	record = db.get_bpa_individualizado(record_id)
	return Response(record, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
def bpa_individualizado_detail(request, record_id: int):
	db = get_bpa_database()
	if request.method == "GET":
		record = db.get_bpa_individualizado(record_id)
		if not record:
			return Response(status=status.HTTP_404_NOT_FOUND)
		return Response(record)

	if db.delete_bpa_individualizado(record_id):
		return Response({"message": "Registro removido"})
	return Response({"detail": "Registro nao encontrado"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET", "POST"])
def bpa_consolidado(request):
	if request.method == "GET":
		competencia = request.query_params.get("competencia")
		if not competencia:
			return Response(
				{"detail": "competencia obrigatoria"},
				status=status.HTTP_400_BAD_REQUEST,
			)
		db = get_bpa_database()
		records = db.list_bpa_consolidado(request.user.cnes, competencia)
		return Response(records)

	data = request.data
	bpa_data = {
		**data,
		"cnes": request.user.cnes,
	}
	db = get_bpa_database()
	record_id = db.save_bpa_consolidado(bpa_data)
	records = db.list_bpa_consolidado(request.user.cnes, data.get("competencia"))
	record = next((item for item in records if item.get("id") == record_id), None)
	return Response(record, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def export_bpa(request):
	data = request.data
	cnes = data.get("cnes") or request.user.cnes
	competencia = data.get("competencia")
	tipo = (data.get("tipo") or "all").upper().replace("-", "").replace("_", "")
	apenas_nao_exportados = bool(data.get("apenas_nao_exportados"))

	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from exporter import FirebirdExporter

	exporter = FirebirdExporter()
	if tipo in {"BPAI", "INDIVIDUALIZADO", "I"}:
		result = exporter.export_bpai(cnes, competencia, apenas_nao_exportados)
	elif tipo in {"BPAC", "CONSOLIDADO", "C"}:
		result = exporter.export_bpac(cnes, competencia)
	else:
		result = exporter.export_all(cnes, competencia)

	if result.get("filename"):
		result["download_url"] = f"/api/export/download/{result['filename']}"

	result["total_registros"] = result.get("total", 0)
	result["arquivo"] = result.get("filename", "")
	return Response(result)


@api_view(["GET"])
def export_download(request, filename: str):
	from exporter import FirebirdExporter

	exporter = FirebirdExporter()
	filepath = os.path.join(exporter.output_dir, filename)
	if not os.path.exists(filepath):
		return Response({"detail": "Arquivo nao encontrado"}, status=status.HTTP_404_NOT_FOUND)
	return FileResponse(open(filepath, "rb"), content_type="application/sql", filename=filename)


@api_view(["GET"])
def export_list(request):
	from exporter import FirebirdExporter

	exporter = FirebirdExporter()
	return Response(exporter.list_exports())


@api_view(["POST"])
def export_reset(request):
	data = request.data
	cnes = data.get("cnes") or request.user.cnes
	competencia = data.get("competencia")
	tipo = data.get("tipo") or "all"
	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	db = get_bpa_database()
	result = db.reset_export_status(cnes, competencia, tipo)
	return Response(
		{
			"success": True,
			"cnes": cnes,
			"competencia": competencia,
			"tipo": tipo,
			"bpai_reset": result.get("bpai_reset", 0),
			"bpac_reset": result.get("bpac_reset", 0),
		}
	)


@api_view(["POST"])
def julia_import(request):
	data = request.data
	tipo = data.get("tipo")
	competencia = data.get("competencia")
	registros = data.get("registros") or []
	if not tipo or not competencia:
		return Response(
			{"detail": "tipo e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	db = get_bpa_database()
	imported = 0
	errors = []
	for idx, reg in enumerate(registros, start=1):
		try:
			if tipo == "BPA-I":
				record = {
					"prd_uid": request.user.cnes,
					"prd_cmp": competencia,
					"prd_cnsmed": reg.get("cns_profissional"),
					"prd_cbo": reg.get("cbo"),
					"prd_ine": reg.get("equipe_ine"),
					"prd_cnspac": reg.get("cns_paciente"),
					"prd_nmpac": (reg.get("nome_paciente", "") or "")[:30].upper(),
					"prd_dtnasc": reg.get("data_nascimento"),
					"prd_sexo": reg.get("sexo"),
					"prd_raca": reg.get("raca_cor", "99"),
					"prd_ibge": reg.get("municipio_ibge"),
					"prd_dtaten": reg.get("data_atendimento"),
					"prd_pa": reg.get("procedimento"),
					"prd_qt_p": reg.get("quantidade", 1),
					"prd_cid": reg.get("cid"),
					"prd_org": "JULIA",
				}
				db.save_bpa_individualizado(record)
			else:
				record = {
					"prd_uid": request.user.cnes,
					"prd_cmp": competencia,
					"prd_cnsmed": reg.get("cns_profissional"),
					"prd_cbo": reg.get("cbo"),
					"prd_pa": reg.get("procedimento"),
					"prd_idade": reg.get("idade", "999"),
					"prd_qt_p": reg.get("quantidade", 1),
					"prd_org": "JULIA",
				}
				db.save_bpa_consolidado(record)
			imported += 1
		except Exception as exc:
			errors.append(f"Reg {idx}: {exc}")

	status_value = "success" if not errors else "partial"
	return Response(
		{
			"status": status_value,
			"message": f"Importados {imported}/{len(registros)}",
			"total_recebidos": len(registros),
			"total_importados": imported,
			"erros": errors[:10],
		}
	)


@api_view(["POST"])
@permission_classes([AllowAny])
def julia_check_connection(request):
	return Response({"success": True, "message": "OK"})


@api_view(["GET"])
@permission_classes([AllowAny])
def referencias_raca_cor(request):
	return Response(
		[
			{"codigo": "01", "descricao": "Branca"},
			{"codigo": "02", "descricao": "Preta"},
			{"codigo": "03", "descricao": "Parda"},
			{"codigo": "04", "descricao": "Amarela"},
			{"codigo": "05", "descricao": "Indigena"},
			{"codigo": "99", "descricao": "Sem informacao"},
		]
	)


@api_view(["GET"])
@permission_classes([AllowAny])
def referencias_sexo(request):
	return Response(
		[
			{"codigo": "M", "descricao": "Masculino"},
			{"codigo": "F", "descricao": "Feminino"},
		]
	)


@api_view(["GET"])
@permission_classes([AllowAny])
def referencias_carater(request):
	return Response(
		[
			{"codigo": "01", "descricao": "Eletivo"},
			{"codigo": "02", "descricao": "Urgencia"},
		]
	)


EXTENSOES_MES = {
	"01": "JAN",
	"02": "FEV",
	"03": "MAR",
	"04": "ABR",
	"05": "MAI",
	"06": "JUN",
	"07": "JUL",
	"08": "AGO",
	"09": "SET",
	"10": "OUT",
	"11": "NOV",
	"12": "DEZ",
}


@api_view(["POST"])
def reports_generate(request):
	data = request.data
	cnes = data.get("cnes") or request.user.cnes
	competencia = data.get("competencia")
	sigla = data.get("sigla") or "CAPSAD"
	tipo = data.get("tipo") or "all"
	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	mes = competencia[4:6] if len(competencia) == 6 else "01"
	extensao = EXTENSOES_MES.get(mes, "TXT")

	db = get_bpa_database()
	bpai_records = db.list_bpa_individualizado(cnes, competencia, limit=10000)
	bpac_records = db.list_bpa_consolidado(cnes, competencia, limit=10000)

	if not bpai_records and not bpac_records:
		return Response(
			{
				"success": False,
				"message": f"Nenhum registro encontrado para competencia {competencia}",
				"stats": {"bpai_count": 0, "bpac_count": 0},
				"files": {},
			}
		)

	sigtap_parser = None
	try:
		from services.sigtap_parser import SigtapParser

		sigtap_dir = os.path.join(
			Path(__file__).resolve().parents[2],
			"BPA-main",
			"TabelaUnificada_202512_v2601161858",
		)
		if os.path.exists(sigtap_dir):
			sigtap_parser = SigtapParser(sigtap_dir)
	except Exception:
		sigtap_parser = None

	from services.bpa_report_generator import BPAExportConfig, BPAFileGenerator
	from constants.estabelecimentos import get_ibge_municipio

	ibge_municipio = get_ibge_municipio(cnes)
	config = BPAExportConfig(
		cnes=cnes,
		competencia=competencia,
		sigla=sigla,
		ibge_municipio=ibge_municipio,
	)
	generator = BPAFileGenerator(config, sigtap_parser=sigtap_parser)

	set_content, total_registros, total_bpas = generator.generate_set_file(
		bpai_records, bpac_records
	)
	campo_controle = str((total_registros * 7 + total_bpas * 3) % 10000).zfill(4)
	relexp_content = generator.generate_relexp(total_registros, total_bpas, campo_controle, extensao)
	bpai_rel_content = generator.generate_bpai_report(bpai_records)
	bpac_rel_content = generator.generate_bpac_report(bpac_records)

	reports_dir = Path(__file__).resolve().parents[2] / "backend" / "reports"
	reports_dir.mkdir(exist_ok=True)
	export_dir = reports_dir / f"{cnes}_{competencia}"
	export_dir.mkdir(exist_ok=True)

	files = {}
	gerar_remessa = tipo in {"remessa", "all"}
	gerar_relexp = tipo in {"remessa", "relexp", "all"}
	gerar_bpai = tipo in {"bpai", "all"}
	gerar_bpac = tipo in {"bpac", "all"}

	if gerar_remessa:
		set_filename = f"PA{sigla}.{extensao}"
		with open(export_dir / set_filename, "w", encoding="latin-1") as handle:
			handle.write(set_content)
		files[set_filename] = f"/api/reports/download/{cnes}_{competencia}/{set_filename}"

	if gerar_relexp:
		with open(export_dir / "RELEXP.PRN", "w", encoding="latin-1") as handle:
			handle.write(relexp_content)
		files["RELEXP.PRN"] = f"/api/reports/download/{cnes}_{competencia}/RELEXP.PRN"

	if gerar_bpai:
		with open(export_dir / "BPAI_REL.TXT", "w", encoding="latin-1") as handle:
			handle.write(bpai_rel_content)
		files["BPAI_REL.TXT"] = f"/api/reports/download/{cnes}_{competencia}/BPAI_REL.TXT"

	if gerar_bpac:
		with open(export_dir / "BPAC_REL.TXT", "w", encoding="latin-1") as handle:
			handle.write(bpac_rel_content)
		files["BPAC_REL.TXT"] = f"/api/reports/download/{cnes}_{competencia}/BPAC_REL.TXT"

	tipo_msg = {
		"remessa": "Arquivo de remessa",
		"relexp": "Relatorio de controle",
		"bpai": "Relatorio BPA-I",
		"bpac": "Relatorio BPA-C",
		"all": "Relatorios",
	}

	return Response(
		{
			"success": True,
			"message": f"{tipo_msg.get(tipo, 'Relatorios')} gerado(s) com sucesso para competencia {competencia}",
			"stats": {
				"total_registros": total_registros,
				"total_bpas": total_bpas,
				"bpai_count": len(bpai_records),
				"bpac_count": len(bpac_records),
				"campo_controle": campo_controle,
			},
			"files": files,
		}
	)


@api_view(["GET"])
def reports_download(request, folder: str, filename: str):
	reports_dir = Path(__file__).resolve().parents[2] / "backend" / "reports"
	filepath = reports_dir / folder / filename
	if not filepath.exists():
		return Response({"detail": "Arquivo nao encontrado"}, status=status.HTTP_404_NOT_FOUND)

	ext = filename.split(".")[-1].upper() if "." in filename else ""
	if ext in EXTENSOES_MES.values() or filename.endswith(".PRN") or filename.endswith(".TXT"):
		media_type = "text/plain"
	else:
		media_type = "application/octet-stream"

	return FileResponse(open(filepath, "rb"), content_type=media_type, filename=filename)


@api_view(["GET"])
def reports_list(request):
	reports_dir = Path(__file__).resolve().parents[2] / "backend" / "reports"
	if not reports_dir.exists():
		return Response({"reports": []})

	reports = []
	for folder in os.listdir(reports_dir):
		folder_path = reports_dir / folder
		if not folder_path.is_dir():
			continue

		files = []
		for filename in os.listdir(folder_path):
			files.append(
				{
					"name": filename,
					"download_url": f"/api/reports/download/{folder}/{filename}",
				}
			)

		reports.append({"folder": folder, "files": files})

	return Response({"reports": reports})


@api_view(["GET"])
def biserver_test_connection(request):
	from services.biserver_client import get_extraction_service

	service = get_extraction_service()
	return Response(service.test_api_connection())


@api_view(["POST"])
def biserver_extract(request):
	data = request.data
	cnes = data.get("cnes")
	competencia = data.get("competencia")
	tipo = data.get("tipo", "bpa_i")
	limit = int(data.get("limit", 100))
	offset = int(data.get("offset", 0))

	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.biserver_client import get_extraction_service

	service = get_extraction_service()
	if tipo == "bpa_i":
		result = service.extract_bpa_individualizado(
			cnes=cnes,
			competencia=competencia,
			limit=limit,
			offset=offset,
		)
	elif tipo == "bpa_c":
		result = service.extract_bpa_consolidado(
			cnes=cnes,
			competencia=competencia,
			limit=limit,
			offset=offset,
		)
	else:
		return Response(
			{"detail": "Tipo deve ser 'bpa_i' ou 'bpa_c'"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	return Response(
		{
			"success": result.success,
			"message": result.message,
			"total_records": result.total_records,
			"records": result.records,
			"errors": result.errors,
		}
	)


@api_view(["POST"])
def biserver_extract_profissionais(request):
	cnes = request.query_params.get("cnes")
	limit = int(request.query_params.get("limit", "50"))
	if not cnes:
		return Response(
			{"detail": "cnes obrigatorio"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.biserver_client import get_extraction_service

	service = get_extraction_service()
	result = service.extract_profissionais(cnes=cnes, limit=limit)
	return Response(result)


@api_view(["GET"])
def biserver_count(request):
	cnes = request.query_params.get("cnes")
	competencia = request.query_params.get("competencia")
	tipo = request.query_params.get("tipo", "bpa_i")
	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.biserver_client import get_extraction_service

	service = get_extraction_service()
	result = service.count_records(cnes=cnes, competencia=competencia, tipo=tipo)
	return Response(result)


@api_view(["POST"])
def biserver_extract_pacientes(request):
	cnes = request.query_params.get("cnes")
	limit = int(request.query_params.get("limit", "100"))
	if not cnes:
		return Response(
			{"detail": "cnes obrigatorio"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.biserver_client import get_extraction_service

	service = get_extraction_service()
	result = service.extract_pacientes(cnes=cnes, limit=limit)
	return Response(result)


@api_view(["POST"])
def biserver_extract_all(request):
	cnes = request.query_params.get("cnes")
	competencia = request.query_params.get("competencia")
	tipo = request.query_params.get("tipo", "bpa_i")
	batch_size = int(request.query_params.get("batch_size", "5000"))
	auto_save = str(request.query_params.get("auto_save", "true")).lower() in {"1", "true", "yes"}
	sigtap_filter = str(request.query_params.get("sigtap_filter", "true")).lower() in {"1", "true", "yes"}

	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.biserver_client import BiServerExtractionService
	from services.corrections import BPACorrections
	from database import BPADatabase

	service = BiServerExtractionService(enable_sigtap_validation=sigtap_filter)

	def save_batch(batch_num, total_batches, records):
		if auto_save and records:
			corrector = BPACorrections(cnes)
			tipo_correcao = "BPI" if tipo == "bpa_i" else "BPA"
			records, _stats = corrector.process_batch(records, tipo_correcao)
			db = BPADatabase()
			if tipo == "bpa_i":
				db.save_bpa_individualizado(records)
			else:
				db.save_bpa_consolidado(records)

	if tipo == "bpa_i":
		result = service.extract_all_bpa_individualizado(
			cnes=cnes,
			competencia=competencia,
			batch_size=batch_size,
			on_batch_complete=save_batch if auto_save else None,
		)
	else:
		result = service.extract_all_bpa_consolidado(
			cnes=cnes,
			competencia=competencia,
			batch_size=batch_size,
			on_batch_complete=save_batch if auto_save else None,
		)

	return Response({**result, "auto_saved": auto_save, "tipo": tipo})


@api_view(["POST"])
def biserver_extract_and_separate(request):
	cnes = request.query_params.get("cnes")
	competencia = request.query_params.get("competencia")
	limit = request.query_params.get("limit")
	offset = int(request.query_params.get("offset", "0"))
	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	limit_value = int(limit) if limit is not None else None

	from collections import Counter
	import time
	from services.biserver_client import get_extraction_service
	from services.corrections import BPACorrections
	from services.sigtap_parser import SigtapParser
	from database import BPADatabase

	inicio = time.time()
	max_errors = 25
	stopped_early = False
	truncation_counts = {}

	sigtap_dir = os.getenv(
		"SIGTAP_DIR",
		str(Path(__file__).resolve().parents[2] / "BPA-main" / "TabelaUnificada_202512_v2601161858"),
	)
	if not os.path.isdir(sigtap_dir):
		msg = f"Diretorio SIGTAP nao encontrado: {sigtap_dir}"
		return Response({"detail": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	sigtap_parser = SigtapParser(sigtap_dir)
	try:
		procs_map = {
			p["CO_PROCEDIMENTO"]: p["NO_PROCEDIMENTO"] for p in sigtap_parser.parse_procedimentos()
		}
	except Exception:
		procs_map = {}

	service = get_extraction_service()
	result = service.extract_and_separate_bpa(
		cnes=cnes,
		competencia=competencia,
		limit=limit_value,
		offset=offset,
	)
	if not result.get("success"):
		return Response(
			{"success": False, "message": result.get("error", "Erro na extracao"), "stats": {}},
			status=status.HTTP_500_INTERNAL_SERVER_ERROR,
		)

	corrector = BPACorrections(cnes)
	stats_corr_bpi = None
	stats_corr_bpc = None

	if result.get("bpa_i"):
		result["bpa_i"], stats_corr_bpi = corrector.process_batch(result["bpa_i"], "BPI")
	else:
		stats_corr_bpi = {
			"total_input": 0,
			"total_output": 0,
			"deleted": 0,
			"corrected": 0,
			"unchanged": 0,
			"delete_reasons": {},
			"correction_types": {},
		}

	if result.get("bpa_c"):
		result["bpa_c"], stats_corr_bpc = corrector.process_batch(result["bpa_c"], "BPA")
	else:
		stats_corr_bpc = {
			"total_input": 0,
			"total_output": 0,
			"deleted": 0,
			"corrected": 0,
			"unchanged": 0,
			"delete_reasons": {},
			"correction_types": {},
		}

	db = BPADatabase()
	saved_bpa_i = 0
	saved_bpa_c = 0
	errors = []

	procedimentos_counter_i = Counter()
	procedimentos_counter_c = Counter()
	profissionais_counter = Counter()
	distribuicao_dias = Counter()
	valor_total_bpa_i = 0.0
	valor_total_bpa_c = 0.0

	def _register_truncation(field_name: str, length: int):
		truncation_counts[field_name] = truncation_counts.get(field_name, 0) + 1

	def sanitize_digits(value, max_len: int, field_name: str) -> str:
		raw = str(value or "")
		digits = "".join(ch for ch in raw if ch.isdigit())
		if len(digits) > max_len:
			_register_truncation(field_name, len(digits))
		return digits[:max_len]

	def sanitize_text(value, max_len: int, field_name: str) -> str:
		raw = str(value or "")
		if len(raw) > max_len:
			_register_truncation(field_name, len(raw))
		return raw[:max_len]

	CNES_URGENCIA = ["2755289", "2492555", "2829606"]
	carater = "02" if cnes in CNES_URGENCIA else "01"

	for record in result.get("bpa_i", []):
		if len(errors) >= max_errors:
			stopped_early = True
			break

		try:
			procedimento = sanitize_digits(record.get("procedimento"), 10, "procedimento")
			procedimento_nome = procs_map.get(procedimento, "")
			quantidade = int(record.get("quantidade") or 1)
			valor = float(record.get("valor_total") or 0)

			db.save_bpa_individualizado(
				{
					"prd_uid": cnes,
					"prd_cmp": competencia,
					"prd_cnsmed": sanitize_digits(record.get("cns_profissional"), 15, "cns_profissional"),
					"prd_cbo": sanitize_digits(record.get("cbo"), 6, "cbo"),
					"prd_ine": sanitize_digits(record.get("ine"), 10, "ine"),
					"prd_cnspac": sanitize_digits(record.get("cns_paciente"), 15, "cns_paciente"),
					"prd_cpf_pcnte": sanitize_digits(record.get("cpf_paciente"), 11, "cpf_paciente"),
					"prd_nmpac": sanitize_text(record.get("nome_paciente"), 255, "nome_paciente"),
					"prd_dtnasc": sanitize_digits(record.get("data_nascimento"), 8, "data_nascimento"),
					"prd_sexo": sanitize_text(record.get("sexo"), 1, "sexo"),
					"prd_raca": sanitize_digits(record.get("raca_cor"), 2, "raca_cor"),
					"prd_ibge": sanitize_digits(record.get("municipio_ibge"), 6, "municipio_ibge"),
					"prd_dtaten": sanitize_digits(record.get("data_atendimento"), 8, "data_atendimento"),
					"prd_pa": procedimento,
					"prd_qt_p": quantidade,
					"prd_cid": sanitize_text(record.get("cid"), 10, "cid"),
					"prd_caten": carater,
					"prd_org": "BISERVER",
				}
			)
			saved_bpa_i += 1
			procedimentos_counter_i[procedimento] += quantidade
			profissionais_counter[record.get("cns_profissional")] += quantidade
			distribuicao_dias[record.get("data_atendimento")] += quantidade
			valor_total_bpa_i += valor
		except Exception as exc:
			errors.append(str(exc))

	for record in result.get("bpa_c", []):
		if len(errors) >= max_errors:
			stopped_early = True
			break
		try:
			procedimento = sanitize_digits(record.get("procedimento"), 10, "procedimento")
			quantidade = int(record.get("quantidade") or 1)
			valor = float(record.get("valor_total") or 0)

			db.save_bpa_consolidado(
				{
					"prd_uid": cnes,
					"prd_cmp": competencia,
					"prd_cnsmed": sanitize_digits(record.get("cns_profissional"), 15, "cns_profissional"),
					"prd_cbo": sanitize_digits(record.get("cbo"), 6, "cbo"),
					"prd_pa": procedimento,
					"prd_idade": sanitize_digits(record.get("idade"), 3, "idade"),
					"prd_qt_p": quantidade,
					"prd_org": "BISERVER",
				}
			)
			saved_bpa_c += 1
			procedimentos_counter_c[procedimento] += quantidade
			valor_total_bpa_c += valor
		except Exception as exc:
			errors.append(str(exc))

	duracao = int(time.time() - inicio)
	procedimentos_mais_usados = [
		{"codigo": codigo, "quantidade": quantidade}
		for codigo, quantidade in procedimentos_counter_i.most_common(10)
	]

	return Response(
		{
			"success": True,
			"stopped_early": stopped_early,
			"stats": {
				"total": result.get("stats", {}).get("total", 0),
				"removed": result.get("stats", {}).get("removed", 0),
				"saved": {
					"bpa_i": saved_bpa_i,
					"bpa_c": saved_bpa_c,
				},
				"corrections": {"bpai": stats_corr_bpi, "bpac": stats_corr_bpc},
				"valores": {
					"bpa_i": float(valor_total_bpa_i),
					"bpa_c": float(valor_total_bpa_c),
					"total": float(valor_total_bpa_i + valor_total_bpa_c),
				},
				"procedimentos_mais_usados": procedimentos_mais_usados[:5],
				"duracao_segundos": duracao,
			},
			"errors": errors[:10] if errors else [],
			"message": (
				f"Salvos: {saved_bpa_i} BPA-I (R$ {valor_total_bpa_i:.2f}), "
				f"{saved_bpa_c} BPA-C (R$ {valor_total_bpa_c:.2f}). Total: R$ {(valor_total_bpa_i + valor_total_bpa_c):.2f}"
			),
		}
	)


@api_view(["GET"])
@permission_classes([AllowAny])
def biserver_export_options(request):
	return Response(
		{
			"options": [
				{
					"id": "sql",
					"name": "Script SQL",
					"description": "Gera arquivo .sql com INSERTs para importar no Firebird via firebird-sync",
					"recommended": True,
				},
				{
					"id": "csv",
					"name": "CSV",
					"description": "Exporta em CSV para conversao posterior",
					"recommended": False,
				},
			]
		}
	)


@api_view(["POST"])
def consolidation_execute(request):
	cnes = request.query_params.get("cnes")
	competencia = request.query_params.get("competencia")
	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.consolidation_service import get_consolidation_service

	consolidation_service = get_consolidation_service()
	stats = consolidation_service.consolidar_bpai_para_bpac(cnes, competencia)
	return Response(
		{
			"success": True,
			"message": f"Consolidacao concluida para {cnes}/{competencia}",
			"stats": stats,
		}
	)


@api_view(["GET"])
def consolidation_verify_procedure(request, codigo: str):
	from services.consolidation_service import get_consolidation_service

	consolidation_service = get_consolidation_service()
	info = consolidation_service.verificar_procedimento(codigo)
	return Response(info)


@api_view(["GET"])
def consolidation_stats(request):
	cnes = request.query_params.get("cnes")
	competencia = request.query_params.get("competencia")
	if not cnes or not competencia:
		return Response(
			{"detail": "cnes e competencia sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	from services.consolidation_service import get_consolidation_service

	consolidation_service = get_consolidation_service()
	db = get_bpa_database()
	bpai_records = db.list_bpa_individualizado(cnes, competencia, exportado=False)

	stats = {
		"total_bpai": len(bpai_records),
		"pode_consolidar_geral": 0,
		"pode_consolidar_idade": 0,
		"manter_bpai": 0,
		"procedimentos_geral": [],
		"procedimentos_idade": [],
		"procedimentos_manter": [],
	}

	proc_geral = set()
	proc_idade = set()
	proc_manter = set()

	for record in bpai_records:
		procedimento = record.get("prd_pa", "")
		info = consolidation_service.verificar_procedimento(procedimento)
		if info["tipo"] == "BPA-C":
			if info["subtipo"] == "geral":
				stats["pode_consolidar_geral"] += 1
				proc_geral.add(procedimento)
			else:
				stats["pode_consolidar_idade"] += 1
				proc_idade.add(procedimento)
		else:
			stats["manter_bpai"] += 1
			proc_manter.add(procedimento)

	stats["procedimentos_geral"] = sorted(proc_geral)
	stats["procedimentos_idade"] = sorted(proc_idade)
	stats["procedimentos_manter"] = sorted(proc_manter)

	return Response(stats)


@api_view(["GET"])
@permission_classes([IsAdminPerfil])
def admin_dashboard_stats(request):
	competencia_inicio = request.query_params.get("competencia_inicio")
	competencia_fim = request.query_params.get("competencia_fim")
	tipo_bpa = request.query_params.get("tipo_bpa")
	cbo = request.query_params.get("cbo")
	procedimento = request.query_params.get("procedimento")

	cnes_list = request.query_params.getlist("cnes")
	if not cnes_list:
		cnes_list = request.query_params.getlist("cnes[]")

	from services.financial_service import get_financial_service

	service = get_financial_service()
	stats = service.get_dashboard_stats(
		competencia_inicio=competencia_inicio,
		competencia_fim=competencia_fim,
		cnes_list=cnes_list or None,
		tipo_bpa=tipo_bpa,
		cbo=cbo,
		procedimento=procedimento,
	)

	return Response({"success": True, **stats})


@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser])
def sigtap_competencias(request):
	from services.sigtap_manager_service import get_sigtap_manager

	manager = get_sigtap_manager()
	if request.method == "GET":
		return Response(
			{
				"active": manager.get_active_competencia(),
				"available": manager.get_available_competencias(),
			}
		)

	competencia = request.data.get("competencia")
	upload = request.FILES.get("file")
	if not competencia or not upload:
		return Response(
			{"detail": "competencia e file sao obrigatorios"},
			status=status.HTTP_400_BAD_REQUEST,
		)
	if not competencia.isdigit() or len(competencia) != 6:
		return Response(
			{"detail": "Competencia deve estar no formato YYYYMM"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	temp_dir = Path("temp_uploads")
	temp_dir.mkdir(exist_ok=True)
	temp_path = temp_dir / upload.name
	with open(temp_path, "wb") as buffer:
		for chunk in upload.chunks():
			buffer.write(chunk)

	try:
		result = manager.import_competencia(str(temp_path), competencia)
		return Response(result)
	finally:
		if temp_path.exists():
			temp_path.unlink()


@api_view(["PUT"])
def sigtap_activate_competencia(request, competencia: str):
	from services.sigtap_manager_service import get_sigtap_manager

	manager = get_sigtap_manager()
	try:
		manager.set_active_competencia(competencia)
	except FileNotFoundError:
		return Response({"detail": "Competencia nao encontrada"}, status=status.HTTP_404_NOT_FOUND)
	return Response({"success": True, "active": competencia})


@api_view(["GET"])
def sigtap_procedimentos(request):
	from services.sigtap_filter_service import get_sigtap_filter_service

	service = get_sigtap_filter_service()
	q = request.query_params.get("q")
	page = int(request.query_params.get("page", "1"))
	limit = int(request.query_params.get("limit", "50"))
	cbo = request.query_params.get("cbo")
	servico = request.query_params.get("servico")
	classificacao = request.query_params.get("classificacao")
	competencia = request.query_params.get("competencia")
	sort_field = request.query_params.get("sort_field")
	sort_order = request.query_params.get("sort_order", "asc")
	tipo_registro = request.query_params.getlist("tipo_registro")

	results = service.get_procedimentos_filtrados(
		tipo_registro=tipo_registro or None,
		cbo=cbo,
		servico=servico,
		classificacao=classificacao,
		termo_busca=q,
		competencia=competencia,
		sort_field=sort_field,
		sort_order=sort_order,
	)

	total = len(results)
	start = (page - 1) * limit
	end = start + limit
	paginated_data = results[start:end]

	return Response(
		{
			"data": paginated_data,
			"total": total,
			"page": page,
			"limit": limit,
			"pages": (total + limit - 1) // limit,
		}
	)


@api_view(["GET"])
def sigtap_estatisticas(request):
	from services.sigtap_filter_service import get_sigtap_filter_service

	competencia = request.query_params.get("competencia")
	service = get_sigtap_filter_service()
	return Response(service.get_estatisticas(competencia))


@api_view(["GET"])
def sigtap_registros(request):
	from services.sigtap_filter_service import get_sigtap_filter_service

	competencia = request.query_params.get("competencia")
	service = get_sigtap_filter_service()
	return Response(service.get_registros(competencia))
