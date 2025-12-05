# config/secrets_manager.py
"""
Módulo para gerenciar secrets do AWS Secrets Manager.
Faz fallback automático para arquivo .env em ambiente de desenvolvimento.
"""
import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


def get_secret_from_aws(secret_name: str = "gamerlink-sm", region_name: str = "us-east-1") -> dict:
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


def load_secrets(use_aws: bool = None) -> None:
    """
    Carrega secrets do AWS Secrets Manager ou do arquivo .env.
    
    A função tenta primeiro buscar do AWS Secrets Manager. Se falhar
    (ex: em desenvolvimento local sem credenciais AWS), faz fallback
    para o arquivo .env.
    
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
            
            # Carrega os secrets no ambiente
            for key, value in secrets.items():
                # Só sobrescreve se a variável não existir no ambiente
                # Isso permite que variáveis de ambiente do sistema tenham prioridade
                if key not in os.environ:
                    os.environ[key] = str(value)
            
            print("✓ Secrets carregados do AWS Secrets Manager")
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

