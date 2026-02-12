from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
	def create_user(self, username: str, password: str | None = None, **extra_fields):
		if not username:
			raise ValueError("username is required")
		user = self.model(username=username, **extra_fields)
		if password:
			user.set_password(password)
		else:
			user.set_unusable_password()
		user.save(using=self._db)
		return user

	def create_superuser(self, username: str, password: str, **extra_fields):
		extra_fields.setdefault("perfil", "admin")
		extra_fields.setdefault("ativo", True)
		user = self.create_user(username, password, **extra_fields)
		return user


class User(AbstractBaseUser):
	"""
	Model mapeado para tabela 'usuarios' existente no PostgreSQL.
	
	Colunas da tabela (conforme DATABASE_MAPPING.md):
	- id: integer (PK, auto-increment)
	- username: varchar(100), unique
	- nome: varchar(255)
	- email: varchar(255), nullable
	- password_hash: varchar(255)
	- cnes: varchar(7), nullable
	- nome_unidade: varchar(255), nullable
	- perfil: varchar(50), default 'digitador'
	- ativo: boolean, default true
	- created_at: timestamp
	- updated_at: timestamp
	- last_login: timestamp, nullable (adicionado para compatibilidade Django)
	"""
	username = models.CharField(max_length=100, unique=True)
	nome = models.CharField(max_length=255)
	email = models.EmailField(max_length=255, blank=True, null=True)
	password = models.CharField(max_length=255, db_column="password_hash")
	cnes = models.CharField(max_length=7, blank=True, null=True)
	nome_unidade = models.CharField(max_length=255, blank=True, null=True)
	perfil = models.CharField(max_length=50, default="digitador")
	ativo = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	# Sobrescreve campo do AbstractBaseUser - coluna será adicionada ao banco
	last_login = models.DateTimeField(blank=True, null=True)

	USERNAME_FIELD = "username"
	REQUIRED_FIELDS = ["nome"]

	objects = UserManager()

	class Meta:
		db_table = "usuarios"
		managed = False

	@property
	def is_active(self) -> bool:
		return self.ativo

	@is_active.setter
	def is_active(self, value: bool) -> None:
		self.ativo = value

	@property
	def is_staff(self) -> bool:
		return self.perfil == "admin"

	@property
	def is_superuser(self) -> bool:
		return self.perfil == "admin"

	@property
	def cbo(self):
		"""
		CBO não está na tabela usuarios, mas em profissionais.
		Retorna None para compatibilidade com código legado.
		Use Profissional.objects.filter(cns=user.cns) para obter o CBO real.
		"""
		return None

	def has_perm(self, perm, obj=None) -> bool:
		return self.is_staff

	def has_module_perms(self, app_label) -> bool:
		return self.is_staff


class Profissional(models.Model):
	cnes = models.CharField(max_length=7)
	cns = models.CharField(max_length=15)
	cpf = models.CharField(max_length=11, blank=True, null=True)
	nome = models.CharField(max_length=255)
	cbo = models.CharField(max_length=6)
	ine = models.CharField(max_length=10, blank=True, null=True)
	vinculo = models.CharField(max_length=50, blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)
	updated_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		db_table = "profissionais"
		managed = False


class Paciente(models.Model):
	cns = models.CharField(max_length=15, unique=True)
	cpf = models.CharField(max_length=11, blank=True, null=True)
	nome = models.CharField(max_length=255)
	data_nascimento = models.CharField(max_length=8, blank=True, null=True)
	sexo = models.CharField(max_length=1, blank=True, null=True)
	raca_cor = models.CharField(max_length=2, blank=True, null=True)
	nacionalidade = models.CharField(max_length=3, blank=True, null=True)
	municipio_ibge = models.CharField(max_length=6, blank=True, null=True)
	cep = models.CharField(max_length=8, blank=True, null=True)
	logradouro_codigo = models.CharField(max_length=10, blank=True, null=True)
	endereco = models.CharField(max_length=255, blank=True, null=True)
	numero = models.CharField(max_length=10, blank=True, null=True)
	complemento = models.CharField(max_length=100, blank=True, null=True)
	bairro = models.CharField(max_length=100, blank=True, null=True)
	telefone = models.CharField(max_length=50, blank=True, null=True)
	email = models.CharField(max_length=255, blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)
	updated_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		db_table = "pacientes"
		managed = False


class BPAIndividualizado(models.Model):
	prd_uid = models.CharField(max_length=7, blank=True, null=True)
	prd_cmp = models.CharField(max_length=6, blank=True, null=True)
	prd_flh = models.IntegerField(blank=True, null=True)
	prd_seq = models.IntegerField(blank=True, null=True)
	prd_cnsmed = models.CharField(max_length=15, blank=True, null=True)
	prd_cbo = models.CharField(max_length=6, blank=True, null=True)
	prd_ine = models.CharField(max_length=10, blank=True, null=True)
	prd_cnspac = models.CharField(max_length=15, blank=True, null=True)
	prd_cpf_pcnte = models.CharField(max_length=11, blank=True, null=True)
	prd_nmpac = models.CharField(max_length=255, blank=True, null=True)
	prd_dtnasc = models.CharField(max_length=8, blank=True, null=True)
	prd_sexo = models.CharField(max_length=1, blank=True, null=True)
	prd_raca = models.CharField(max_length=2, blank=True, null=True)
	prd_nac = models.CharField(max_length=3, blank=True, null=True)
	prd_ibge = models.CharField(max_length=6, blank=True, null=True)
	prd_idade = models.CharField(max_length=3, blank=True, null=True)
	prd_cep_pcnte = models.CharField(max_length=8, blank=True, null=True)
	prd_lograd_pcnte = models.CharField(max_length=10, blank=True, null=True)
	prd_end_pcnte = models.CharField(max_length=255, blank=True, null=True)
	prd_num_pcnte = models.CharField(max_length=10, blank=True, null=True)
	prd_compl_pcnte = models.CharField(max_length=100, blank=True, null=True)
	prd_bairro_pcnte = models.CharField(max_length=100, blank=True, null=True)
	prd_ddtel_pcnte = models.CharField(max_length=2, blank=True, null=True)
	prd_tel_pcnte = models.CharField(max_length=50, blank=True, null=True)
	prd_email_pcnte = models.CharField(max_length=255, blank=True, null=True)
	prd_dtaten = models.CharField(max_length=8, blank=True, null=True)
	prd_pa = models.CharField(max_length=10, blank=True, null=True)
	prd_qt_p = models.IntegerField(blank=True, null=True)
	prd_cid = models.CharField(max_length=10, blank=True, null=True)
	prd_caten = models.CharField(max_length=2, blank=True, null=True)
	prd_naut = models.CharField(max_length=50, blank=True, null=True)
	prd_cnpj = models.CharField(max_length=14, blank=True, null=True)
	prd_servico = models.CharField(max_length=3, blank=True, null=True)
	prd_classificacao = models.CharField(max_length=3, blank=True, null=True)
	prd_etnia = models.CharField(max_length=4, blank=True, null=True)
	prd_eqp_area = models.CharField(max_length=10, blank=True, null=True)
	prd_eqp_seq = models.CharField(max_length=10, blank=True, null=True)
	prd_mvm = models.CharField(max_length=6, blank=True, null=True)
	prd_advqt = models.CharField(max_length=2, blank=True, null=True)
	prd_flpa = models.CharField(max_length=1, blank=True, null=True)
	prd_flcbo = models.CharField(max_length=1, blank=True, null=True)
	prd_flca = models.CharField(max_length=1, blank=True, null=True)
	prd_flida = models.CharField(max_length=1, blank=True, null=True)
	prd_flqt = models.CharField(max_length=1, blank=True, null=True)
	prd_fler = models.CharField(max_length=1, blank=True, null=True)
	prd_flmun = models.CharField(max_length=1, blank=True, null=True)
	prd_flcid = models.CharField(max_length=1, blank=True, null=True)
	prd_org = models.CharField(max_length=10, blank=True, null=True)
	prd_exportado = models.BooleanField(blank=True, null=True)
	data_exportacao = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)
	updated_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		db_table = "bpa_individualizado"
		managed = False


class BPAConsolidado(models.Model):
	prd_uid = models.CharField(max_length=7, blank=True, null=True)
	prd_cmp = models.CharField(max_length=6, blank=True, null=True)
	prd_flh = models.IntegerField(blank=True, null=True)
	prd_cnsmed = models.CharField(max_length=15, blank=True, null=True)
	prd_cbo = models.CharField(max_length=6, blank=True, null=True)
	prd_pa = models.CharField(max_length=10, blank=True, null=True)
	prd_qt_p = models.IntegerField(blank=True, null=True)
	prd_idade = models.CharField(max_length=3, blank=True, null=True)
	prd_org = models.CharField(max_length=10, blank=True, null=True)
	prd_exportado = models.BooleanField(blank=True, null=True)
	data_exportacao = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)
	updated_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		db_table = "bpa_consolidado"
		managed = False


class Exportacao(models.Model):
	cnes = models.CharField(max_length=7)
	competencia = models.CharField(max_length=6)
	tipo = models.CharField(max_length=10)
	arquivo = models.CharField(max_length=255, blank=True, null=True)
	total_registros = models.IntegerField(blank=True, null=True)
	status = models.CharField(max_length=20, blank=True, null=True)
	erro = models.TextField(blank=True, null=True)
	usuario_id = models.IntegerField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		db_table = "exportacoes"
		managed = False


class HistoricoExtracao(models.Model):
	cnes = models.CharField(max_length=7)
	competencia = models.CharField(max_length=6)
	total_bpa_i = models.IntegerField(blank=True, null=True)
	total_bpa_c = models.IntegerField(blank=True, null=True)
	total_removido = models.IntegerField(blank=True, null=True)
	total_geral = models.IntegerField(blank=True, null=True)
	valor_total_bpa_i = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
	valor_total_bpa_c = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
	valor_total_geral = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
	procedimentos_mais_usados = models.JSONField(blank=True, null=True)
	profissionais_mais_ativos = models.JSONField(blank=True, null=True)
	distribuicao_por_dia = models.JSONField(blank=True, null=True)
	usuario_id = models.IntegerField(blank=True, null=True)
	duracao_segundos = models.IntegerField(blank=True, null=True)
	status = models.CharField(max_length=20, blank=True, null=True)
	erro = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		db_table = "historico_extracoes"
		managed = False

	def get_full_name(self) -> str:
		return self.nome

	def get_short_name(self) -> str:
		return self.nome.split(" ", 1)[0]
