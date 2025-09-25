# 🚀 Setup do Projeto Tinder Gamer

## 📋 Pré-requisitos
- Docker
- Docker Compose

## ⚙️ Configuração

### 1. Clone o repositório
```bash
git clone <seu-repositorio>
cd SD
```

### 2. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env com suas configurações
# IMPORTANTE: Mude a SECRET_KEY para algo aleatório!
```

### 3. Execute o projeto
```bash
# Subir os containers
docker-compose up -d

# Executar migrações (primeira vez)
docker-compose exec api alembic upgrade head

# Verificar se está funcionando
curl http://localhost:8000/
```

## 🌐 URLs Disponíveis
- **API:** http://localhost:8000
- **Documentação:** http://localhost:8000/docs
- **Banco:** localhost:5432

## 🧪 Testando a API

### Registro de usuário:
```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "teste@exemplo.com", "password": "123456"}'
```

### Login:
```bash
curl -X POST "http://localhost:8000/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=teste@exemplo.com&password=123456"
```

## 🔧 Comandos Úteis
```bash
# Ver logs
docker-compose logs -f api

# Parar containers
docker-compose down

# Rebuild (se mudar requirements.txt)
docker-compose build --no-cache
```
