# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth as auth_router
from dotenv import load_dotenv
from database.connection import engine
from database import models

# Carrega as variáveis de ambiente ANTES de qualquer outro código do app.
# Isso garante que elas estarão disponíveis para todos os módulos.
load_dotenv()

# Cria as tabelas no banco de dados (alternativa ao Alembic para dev)
# Em produção, você usaria apenas as migrações do Alembic.
# models.Base.metadata.create_all(bind=engine) # Descomente se precisar criar tabelas sem Alembic

app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos
    allow_headers=["*"],  # Permite todos os headers
)

# Inclui o router de autenticação na sua aplicação
app.include_router(auth_router.router)

# Servir arquivos estáticos do frontend
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Rota para servir o frontend na raiz
@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

# Rota para servir recommendations
@app.get("/recommendations")
async def recommendations():
    return FileResponse("frontend/recommendations.html")

# Rota da API (mantém separada)
@app.get("/api")
def api_info():
    return {"message": "Welcome to the API"}