# config/__init__.py
"""
Módulo centralizado para gerenciamento de secrets e variáveis de ambiente.
Suporta AWS Secrets Manager com fallback para arquivo .env em desenvolvimento.
"""
from .secrets_manager import load_secrets

__all__ = ["load_secrets"]

