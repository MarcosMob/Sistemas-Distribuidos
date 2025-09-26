#  Deploy na AWS EC2 - Guia Completo

##  Pré-requisitos

1. **Conta AWS** ativa
2. **Repositório GitHub** com seu código
3. **Conhecimento básico** de terminal/SSH

##  Passo 1: Criar Instância EC2

### 1.1 Acessar AWS Console
- Vá para [AWS Console](https://console.aws.amazon.com)
- Procure por "EC2" e clique

### 1.2 Lançar Instância
- Clique em "Launch Instance"
- **Nome:** `tinder-gamer-server`
- **AMI:** Ubuntu Server 22.04 LTS (Free tier)
- **Instance Type:** t3.micro (Free tier)
- **Key Pair:** Crie um novo ou use existente
- **Security Group:** Crie novo com estas regras:

| Tipo | Protocolo | Porta | Origem | Descrição |
|------|-----------|------|--------|-----------|
| SSH | TCP | 22 | Meu IP | Acesso SSH |
| HTTP | TCP | 8000 | 0.0.0.0/0 | Aplicação web |
| Custom | TCP | 5432 | 0.0.0.0/0 | PostgreSQL |

- **Storage:** 8 GB (Free tier)
- Clique em "Launch Instance"

### 1.3 Obter IP Público
- Anote o **IPv4 Public IP** da sua instância
- Exemplo: `54.123.45.67`

##  Passo 2: Conectar na EC2

### 2.1 Via SSH (Windows)
```bash
# No PowerShell ou CMD
ssh -i "sua-chave.pem" ubuntu@seu-ip-publico
```

### 2.2 Via SSH (Mac/Linux)
```bash
# Dar permissão à chave
chmod 400 sua-chave.pem

# Conectar
ssh -i "sua-chave.pem" ubuntu@seu-ip-publico
```

##  Passo 3: Instalar Dependências

### 3.1 Atualizar Sistema
```bash
sudo apt update
sudo apt upgrade -y
```

### 3.2 Instalar Docker
```bash
# Instalar Docker
sudo apt install docker.io -y

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Fazer logout e login novamente para aplicar as mudanças
exit
```

### 3.3 Conectar Novamente e Instalar Docker Compose
```bash
# Conectar novamente
ssh -i "sua-chave.pem" ubuntu@seu-ip-publico

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker --version
docker-compose --version
```

### 3.4 Instalar Git
```bash
sudo apt install git -y
```

##  Passo 4: Baixar Código

### 4.1 Clonar Repositório
```bash
# Clonar seu repositório
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 4.2 Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp env.production.example .env.production

# Editar com suas configurações
nano .env.production
```

**Configure estas variáveis:**
```env
POSTGRES_DB=tinder_gamer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=SUA_SENHA_SUPER_SEGURA_AQUI
SECRET_KEY=SUA_CHAVE_JWT_SUPER_SEGURA_AQUI
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
DEBUG=false
```

**Salvar:** `Ctrl + X`, depois `Y`, depois `Enter`

## Passo 5: Deploy da Aplicação

### 5.1 Tornar Script Executável
```bash
chmod +x deploy.sh
```

### 5.2 Executar Deploy
```bash
./deploy.sh
```

**O script vai:**
- Parar containers existentes
- Limpar imagens antigas
- Construir novas imagens
- Iniciar containers
- Verificar status

## Passo 6: Verificar se Funcionou

### 6.1 Verificar Containers
```bash
docker-compose -f docker-compose.prod.yml ps
```

**Deve mostrar:**
```
NAME                     IMAGE                STATUS
tinder_gamer_api_prod    sd-api               Up
tinder_gamer_db_prod     postgres:15-alpine   Up
```

### 6.2 Testar API
```bash
curl http://localhost:8000/api
```

**Deve retornar:**
```json
{"message":"Welcome to the API"}
```

### 6.3 Acessar no Navegador
```
http://seu-ip-publico:8000
```

## Passo 7: Atualizações Futuras

### 7.1 Atualizar Código
```bash
# Na sua máquina local
git add .
git commit -m "Nova feature"
git push origin main
```

### 7.2 Atualizar na EC2
```bash
# Na EC2
git pull origin main
./deploy.sh
```

## Troubleshooting

### Problema: Não consegue conectar via SSH
```bash
# Verificar se a chave tem permissão correta
chmod 400 sua-chave.pem

# Verificar Security Group (porta 22)
# Verificar se a instância está rodando
```

### Problema: Porta 8000 não acessível
```bash
# Verificar Security Group (porta 8000)
# Verificar se containers estão rodando
docker-compose -f docker-compose.prod.yml ps

# Verificar logs
docker-compose -f docker-compose.prod.yml logs api
```

### Problema: Banco não conecta
```bash
# Verificar logs do banco
docker-compose -f docker-compose.prod.yml logs db

# Verificar variáveis de ambiente
cat .env.production
```

### Problema: Container não inicia
```bash
# Verificar logs detalhados
docker-compose -f docker-compose.prod.yml logs --tail=50 api

# Verificar se há erros de build
docker-compose -f docker-compose.prod.yml build --no-cache
```

##  Monitoramento

### Ver Logs em Tempo Real
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Verificar Uso de Recursos
```bash
docker stats
```

### Backup do Banco
```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres tinder_gamer > backup.sql
```

##  Custos

- **EC2 t3.micro:** ~$8-10/mês (Free tier: 12 meses grátis)
- **Storage 8GB:** ~$1/mês (Free tier: 30GB grátis)
- **Total:** ~$9-11/mês (ou GRÁTIS no primeiro ano)

##  Segurança

1. **Use senhas fortes** no `.env.production`
2. **Mantenha a EC2 atualizada:** `sudo apt update && sudo apt upgrade`
3. **Monitore logs regularmente**
4. **Faça backups do banco**
5. **Use HTTPS** (opcional - requer Load Balancer)

---

 **Pronto!** Sua aplicação está rodando na AWS!

**URL:** `http://seu-ip-publico:8000`
