# Etapa 1: Imagem Base
# Começamos com uma imagem oficial do Python, leve e otimizada (slim).
FROM python:3.11-slim

# Etapa 2: Variáveis de Ambiente
# Ajuda o Python a rodar de forma otimizada dentro do container.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Etapa 3: Diretório de Trabalho
# Define o diretório padrão dentro do container. Todos os comandos a seguir
# serão executados a partir daqui.
WORKDIR /app

# Etapa 4: Instalação de Dependências
# Copiamos apenas o requirements.txt primeiro para aproveitar o cache do Docker.
# As dependências só serão reinstaladas se este arquivo mudar.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 5: Copiar o Código da Aplicação
# Copia todo o código do seu projeto para dentro do diretório /app no container.
COPY . .

# Etapa 6: Expor a Porta
# Informa ao Docker que a aplicação dentro do container irá "escutar" na porta 8000.
EXPOSE 8000

# Etapa 7: Comando de Execução
# O comando para iniciar a aplicação quando o container for criado.
# --host 0.0.0.0 é crucial para permitir o acesso de fora do container.
# --reload é ótimo para desenvolvimento, pois reinicia o servidor a cada alteração no código.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]