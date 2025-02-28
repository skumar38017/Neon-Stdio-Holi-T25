import logging
from logging.config import fileConfig
from sqlalchemy import create_engine, engine_from_config, pool
from alembic import context
import psycopg2
from psycopg2 import sql
from app.database.base import Base
from app.database.models import *  # Import all models
from app.config import config  # Import database config
from app.utils.common_icons import event_icons  # Import the event icons

# Alembic Config object
alembic_config = context.config

# Database URLs from config
database_url = config.database_url
async_database_url = config.async_database_url

# Set the database URL in Alembic config
alembic_config.set_main_option("sqlalchemy.url", database_url)

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set log level to DEBUG for development

# Target metadata for Alembic autogenerate
target_metadata = Base.metadata

# Log the start of the script
logging.debug(f"{event_icons['database.connecting']} Starting Alembic migration process...")

def ensure_db_and_role():
    """Check if the PostgreSQL role and database exist, and create them if necessary."""
    admin_db_url = config.database["admin_db_url"]
    role_name = config.database["role"]
    db_name = config.database["db_name"]
    db_password = config.database["password"]

    # Debug configuration values
    logging.debug(f"Role: {role_name}, DB Name: {db_name}, Password: {db_password}")

    # Validate role_name
    if not role_name:
        logging.error(f"{event_icons['database.error']} ❌ Role name is empty. Please check your configuration.")
        return

    try:
        # Connect as superuser to PostgreSQL
        logging.debug(f"{event_icons['database.connecting']} Connecting to the PostgreSQL admin database: {admin_db_url}")
        conn = psycopg2.connect(admin_db_url)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if role exists
        logging.debug(f"{event_icons['database.get']} Checking if role {role_name} exists...")
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s;", (role_name,))
        role_exists = cur.fetchone()

        if not role_exists:
            logging.debug(f"{event_icons['database.create']} Role {role_name} does not exist. Creating role...")
            cur.execute(sql.SQL(
                "CREATE ROLE {role} WITH LOGIN PASSWORD {password};"
            ).format(
                role=sql.Identifier(role_name),
                password=sql.Literal(db_password)
            ))

        # Check if database exists
        logging.debug(f"{event_icons['database.get']} Checking if database {db_name} exists...")
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
        db_exists = cur.fetchone()

        if not db_exists:
            logging.debug(f"{event_icons['database.create']} Database {db_name} does not exist. Creating database...")
            cur.execute(sql.SQL(
                "CREATE DATABASE {dbname} OWNER {role};"
            ).format(
                dbname=sql.Identifier(db_name),
                role=sql.Identifier(role_name)
            ))

        # Grant privileges
        logging.debug(f"{event_icons['database.update']} Granting privileges on database {db_name} to role {role_name}...")
        cur.execute(sql.SQL(
            "GRANT ALL PRIVILEGES ON DATABASE {dbname} TO {role};"
        ).format(
            dbname=sql.Identifier(db_name),
            role=sql.Identifier(role_name)
        ))

        # Alter role permissions
        logging.debug(f"{event_icons['database.update']} Altering role {role_name} permissions...")
        cur.execute(sql.SQL(
            "ALTER ROLE {role} WITH SUPERUSER CREATEDB CREATEROLE REPLICATION BYPASSRLS;"
        ).format(
            role=sql.Identifier(role_name)
        ))

        cur.close()
        conn.close()
        logging.debug(f"{event_icons['database.connected']} ✅ Database and role are ready.")

    except Exception as e:
        logging.error(f"{event_icons['database.error']} ❌ Error ensuring DB and role: {e}")
        
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = alembic_config.get_main_option("sqlalchemy.url")
    logging.debug(f"{event_icons['database.connecting']} Running migrations offline with URL: {url}")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    
    # Ensure database & role exist
    ensure_db_and_role()

    logging.debug(f"{event_icons['database.connecting']} Connecting to the database to run migrations online...")
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    logging.debug(f"{event_icons['database.connecting']} Running in offline mode.")
    run_migrations_offline()
else:
    logging.debug(f"{event_icons['database.connecting']} Running in online mode.")
    run_migrations_online()

logging.debug(f"{event_icons['database.connected']} Alembic migration process completed.")
