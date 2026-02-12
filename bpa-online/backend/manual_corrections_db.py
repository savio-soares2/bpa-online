import os
import sys
import logging
import argparse
from typing import List, Tuple
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

# Constrói DATABASE_URL se não existir mas houver variáveis individuais
if not os.getenv("DATABASE_URL") and os.getenv("DB_USER"):
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "bpa_online")

    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    os.environ["DATABASE_URL"] = db_url
    print(f"Configurando DATABASE_URL via .env: postgresql://{user}:***@{host}:{port}/{dbname}")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


DEFAULT_LOGRADOURO = "077"


def parse_ids(value: str) -> List[int]:
    if not value:
        return []
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return [int(p) for p in parts]


def build_filters(args: argparse.Namespace, table: str) -> Tuple[str, List]:
    clauses = []
    params: List = []

    if args.ids:
        clauses.append("id = ANY(%s)")
        params.append(args.ids)

    if table == "bpa_individualizado":
        if args.cnes:
            clauses.append("prd_uid = %s")
            params.append(args.cnes)
        if args.competencia:
            clauses.append("prd_cmp = %s")
            params.append(args.competencia)

    if clauses:
        return " AND " + " AND ".join(clauses), params
    return "", params


def count_invalid_sexo(table: str, filters_sql: str, params: List) -> int:
    if table == "bpa_individualizado":
        col = "prd_sexo"
    else:
        col = "sexo"

    sql = f"""
        SELECT COUNT(*)
        FROM {table}
        WHERE (
            {col} IS NULL OR {col} = '' OR {col} IN ('0','1') OR UPPER({col}) NOT IN ('M','F')
        )
        {filters_sql}
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return int(cursor.fetchone()[0])


def count_invalid_logradouro(table: str, filters_sql: str, params: List) -> int:
    if table == "bpa_individualizado":
        col = "prd_lograd_pcnte"
    else:
        col = "logradouro_codigo"

    sql = f"""
        SELECT COUNT(*)
        FROM {table}
        WHERE ({col} IS NULL OR TRIM({col}) = '')
        {filters_sql}
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return int(cursor.fetchone()[0])


def update_sexo(table: str, filters_sql: str, params: List) -> int:
    if table == "bpa_individualizado":
        col = "prd_sexo"
    else:
        col = "sexo"

    sql = f"""
        UPDATE {table}
        SET {col} = CASE
            WHEN {col} = '0' THEN 'M'
            WHEN {col} = '1' THEN 'F'
            WHEN UPPER({col}) = 'M' THEN 'M'
            WHEN UPPER({col}) = 'F' THEN 'F'
            ELSE 'M'
        END,
        updated_at = CURRENT_TIMESTAMP
        WHERE (
            {col} IS NULL OR {col} = '' OR {col} IN ('0','1') OR UPPER({col}) NOT IN ('M','F')
        )
        {filters_sql}
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount


def update_logradouro(table: str, filters_sql: str, params: List) -> int:
    if table == "bpa_individualizado":
        col = "prd_lograd_pcnte"
    else:
        col = "logradouro_codigo"

    sql = f"""
        UPDATE {table}
        SET {col} = %s,
        updated_at = CURRENT_TIMESTAMP
        WHERE ({col} IS NULL OR TRIM({col}) = '')
        {filters_sql}
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, [DEFAULT_LOGRADOURO] + params)
            conn.commit()
            return cursor.rowcount


def fetch_samples(table: str, filters_sql: str, params: List, limit: int) -> List[tuple]:
    if table == "bpa_individualizado":
        sql = f"""
            SELECT id, prd_uid, prd_cmp, prd_sexo, prd_lograd_pcnte
            FROM {table}
            WHERE (
                prd_sexo IS NULL OR prd_sexo = '' OR prd_sexo IN ('0','1') OR UPPER(prd_sexo) NOT IN ('M','F')
                OR prd_lograd_pcnte IS NULL OR TRIM(prd_lograd_pcnte) = ''
            )
            {filters_sql}
            ORDER BY id
            LIMIT %s
        """
    else:
        sql = f"""
            SELECT id, sexo, logradouro_codigo
            FROM {table}
            WHERE (
                sexo IS NULL OR sexo = '' OR sexo IN ('0','1') OR UPPER(sexo) NOT IN ('M','F')
                OR logradouro_codigo IS NULL OR TRIM(logradouro_codigo) = ''
            )
            {filters_sql}
            ORDER BY id
            LIMIT %s
        """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params + [limit])
            return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(
        description="Correção manual de sexo e logradouro no PostgreSQL (BPA Online)."
    )
    parser.add_argument("--table", choices=["bpa_individualizado", "pacientes"], default="bpa_individualizado")
    parser.add_argument("--cnes", help="CNES para filtrar (apenas BPA-I)")
    parser.add_argument("--competencia", help="Competência para filtrar (apenas BPA-I)")
    parser.add_argument("--ids", type=parse_ids, help="IDs separados por vírgula")
    parser.add_argument("--apply", action="store_true", help="Aplicar correções (default: dry-run)")
    parser.add_argument("--sample", type=int, default=0, help="Mostrar amostra de registros afetados")

    args = parser.parse_args()

    filters_sql, params = build_filters(args, args.table)

    count_sexo = count_invalid_sexo(args.table, filters_sql, params)
    count_logradouro = count_invalid_logradouro(args.table, filters_sql, params)

    logger.info(f"Tabela: {args.table}")
    logger.info(f"Registros com sexo inválido/vazio: {count_sexo}")
    logger.info(f"Registros com logradouro vazio: {count_logradouro}")

    if args.sample and args.sample > 0:
        samples = fetch_samples(args.table, filters_sql, params, args.sample)
        logger.info(f"Amostra ({len(samples)} registros):")
        for row in samples:
            logger.info(f"  {row}")

    if not args.apply:
        logger.info("Dry-run concluído. Use --apply para executar as atualizações.")
        return

    updated_sexo = update_sexo(args.table, filters_sql, params)
    updated_logradouro = update_logradouro(args.table, filters_sql, params)

    logger.info(f"Atualizações sexo: {updated_sexo}")
    logger.info(f"Atualizações logradouro: {updated_logradouro}")
    logger.info("Correção manual concluída.")


if __name__ == "__main__":
    main()