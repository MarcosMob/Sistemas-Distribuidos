#!/bin/bash

# Script de deploy para AWS EC2
# Execute este script na sua instância EC2

set -e

echo "🚀 Iniciando deploy do Tinder Gamer..."

# Parar containers existentes
echo "📦 Parando containers existentes..."
docker-compose -f docker-compose.prod.yml down

# Remover imagens antigas (opcional)
echo "🧹 Limpando imagens antigas..."
docker system prune -f

# Construir e iniciar containers
echo "🔨 Construindo e iniciando containers..."
docker-compose -f docker-compose.prod.yml up --build -d

# Verificar se os containers estão rodando
echo "✅ Verificando status dos containers..."
docker-compose -f docker-compose.prod.yml ps

docker-compose exec api alembic upgrade head

# Verificar logs
echo "📋 Últimos logs da API:"
docker-compose -f docker-compose.prod.yml logs --tail=20 api

echo "🎉 Deploy concluído!"
echo "🌐 Sua aplicação está rodando em: http://seu-ip-ec2:8000"
