import os
import sys

# Adiciona o diretório raiz ao path para importar o módulo config
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Carrega secrets do AWS Secrets Manager (com fallback para .env)
from config import load_secrets
load_secrets()

# --- NOSSA LINHA DE DEBUG ---
# print(f"--- DEBUG INFO ---")
# print(f"Caminho do .env tentado: {dotenv_path}")
# print(f"DATABASE_URL lida pelo Alembic: '{os.getenv('DATABASE_URL')}'")
# print(f"--------------------")
# # --- FIM DA LINHA DE DEBUG ---
# # --- NOSSO NOVO DEBUG AVANÇADO ---
# db_url = os.getenv('DATABASE_URL')
# print("--- DEBUG AVANÇADO ---")
# print(f"URL lida (repr): {repr(db_url)}") # repr() mostra caracteres 'escondidos'
# if db_url:
#     print(f"Tamanho da URL: {len(db_url)}")
#     print("Caracteres e seus códigos (ASCII/Unicode):")
#     # Itera sobre cada caractere para encontrar algo estranho
#     for i, char in enumerate(db_url):
#         print(f"  Índice {i}: '{char}' -> Código: {ord(char)}")
# print("------------------------")
# --- FIM DO DEBUG ---

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- A CORREÇÃO DEFINITIVA ---
# Nós vamos ler a URL diretamente do ambiente (onde sabemos que ela existe)
# e vamos forçar essa URL na configuração do Alembic.
db_url_from_env = os.getenv('DATABASE_URL')
if db_url_from_env is None:
    # Se por algum motivo a URL não estiver no ambiente, pare com um erro claro.
    raise ValueError("A variável de ambiente DATABASE_URL não foi encontrada.")

# Sobreponha a configuração 'sqlalchemy.url' com a URL que carregamos do .env
config.set_main_option('sqlalchemy.url', db_url_from_env)
# --- FIM DA CORREÇÃO ---

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from database.models import Base
# e coloque o caminho para a pasta da sua aplicação
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
