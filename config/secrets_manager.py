# config/secrets_manager.py
"""
Módulo para gerenciar secrets do AWS Secrets Manager.
Faz fallback automático para arquivo .env em ambiente de desenvolvimento.
"""
import os
import json
from urllib.parse import quote_plus
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


def get_secret_from_aws(secret_name: str = "gamerlink-sm1", region_name: str = "us-east-1") -> dict:
    """
    Busca secrets do AWS Secrets Manager.
    
    Args:
        secret_name: Nome do secret no AWS Secrets Manager
        region_name: Região AWS onde o secret está armazenado
        
    Returns:
        dict: Dicionário com os secrets parseados do JSON
        
    Raises:
        ClientError: Se houver erro ao buscar o secret
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # Re-raise para que o chamador possa tratar
        raise e

    secret = get_secret_value_response['SecretString']
    
    # Assumindo que o secret está armazenado como JSON
    # Se estiver em outro formato, ajuste aqui
    try:
        return json.loads(secret)
    except json.JSONDecodeError:
        # Se não for JSON, retorna como string única
        # Você pode ajustar isso conforme o formato do seu secret
        return {"SECRET_STRING": secret}


def _build_database_url(secrets: dict) -> str:
    """
    Constrói a DATABASE_URL a partir dos campos individuais do RDS.
    
    O secret do AWS Secrets Manager pode vir no formato RDS (com campos separados)
    ou já com DATABASE_URL pronta. Esta função trata ambos os casos.
    
    Args:
        secrets: Dicionário com os secrets do AWS Secrets Manager
        
    Returns:
        str: URL de conexão do banco de dados no formato PostgreSQL
    """
    # Se já existe DATABASE_URL no secret, usa ela
    if 'DATABASE_URL' in secrets:
        return secrets['DATABASE_URL']
    
    # Se não, constrói a partir dos campos individuais do RDS
    # Formato esperado: postgresql://username:password@host:port/dbname
    username = secrets.get('username', 'postgres')
    password = secrets.get('password', '')
    host = secrets.get('host', 'localhost')
    port = secrets.get('port', 5432)
    dbname = secrets.get('dbname') or secrets.get('dbInstanceIdentifier', 'gamerlink_db')
    
    # Escapar caracteres especiais na senha (se necessário)
    password_escaped = quote_plus(password)
    
    database_url = f"postgresql://{username}:{password_escaped}@{host}:{port}/{dbname}"
    return database_url


def load_secrets(use_aws: bool = None) -> None:
    """
    Carrega secrets do AWS Secrets Manager ou do arquivo .env.
    
    A função tenta primeiro buscar do AWS Secrets Manager. Se falhar
    (ex: em desenvolvimento local sem credenciais AWS), faz fallback
    para o arquivo .env.
    
    Suporta dois formatos de secret:
    1. Formato RDS: com campos separados (username, password, host, port, dbname)
    2. Formato customizado: com DATABASE_URL já pronta
    
    Args:
        use_aws: Se True, força uso do AWS. Se False, força uso do .env.
                 Se None, tenta AWS primeiro e faz fallback para .env.
    """
    # Se explicitamente desabilitado, usa apenas .env
    if use_aws is False:
        load_dotenv()
        return
    
    # Se explicitamente habilitado ou None, tenta AWS primeiro
    if use_aws is True or use_aws is None:
        try:
            # Tenta buscar do AWS Secrets Manager
            secrets = get_secret_from_aws()
            
            # Construir DATABASE_URL se necessário
            if 'DATABASE_URL' not in secrets or not secrets.get('DATABASE_URL'):
                database_url = _build_database_url(secrets)
                secrets['DATABASE_URL'] = database_url
            
            # Mapear campos do RDS para variáveis de ambiente padrão
            # (caso o código espere nomes diferentes)
            env_vars = {
                'DATABASE_URL': secrets['DATABASE_URL'],
                'SECRET_KEY': secrets.get('SECRET_KEY', ''),
                'ALGORITHM': secrets.get('ALGORITHM', 'HS256'),
                'ACCESS_TOKEN_EXPIRE_MINUTES': secrets.get('ACCESS_TOKEN_EXPIRE_MINUTES', '120'),
                'ENVIRONMENT': secrets.get('ENVIRONMENT', 'production'),
                'DEBUG': secrets.get('DEBUG', 'false'),
            }
            
            # Carrega os secrets no ambiente
            for key, value in env_vars.items():
                # Sobrescreve se não existir OU se estiver vazia
                current_value = os.environ.get(key)
                if current_value is None or current_value == "":
                    os.environ[key] = str(value)
            
            print("✓ Secrets carregados do AWS Secrets Manager")
            print(f"  - DATABASE_URL: {secrets['DATABASE_URL'].split('@')[0]}@*** (oculto)")
            print(f"  - ENVIRONMENT: {env_vars['ENVIRONMENT']}")
            return
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            # Se for erro de credenciais ou recurso não encontrado, faz fallback
            if error_code in ['ResourceNotFoundException', 'InvalidRequestException', 
                            'InvalidParameterException', 'DecryptionFailureException',
                            'InternalServiceErrorException', 'AccessDeniedException']:
                print(f"⚠ AWS Secrets Manager não disponível ({error_code}), usando .env como fallback")
            else:
                # Outros erros podem ser críticos, mas ainda fazemos fallback
                print(f"⚠ Erro ao acessar AWS Secrets Manager: {e}, usando .env como fallback")
        except Exception as e:
            # Qualquer outro erro (ex: boto3 não instalado, sem credenciais)
            print(f"⚠ Erro ao inicializar AWS Secrets Manager: {e}, usando .env como fallback")
    
    # Fallback para .env
    load_dotenv()
    print("✓ Variáveis carregadas do arquivo .env")

