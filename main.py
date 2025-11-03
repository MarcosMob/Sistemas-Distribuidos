# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# --- MUDANÇA 1: Limpeza e centralização das importações dos routers ---
# Importe todos os módulos de rotas que você vai usar.
from routers import auth, match, chat 

from database.connection import engine
from database import models

# Carrega as variáveis de ambiente
load_dotenv()

# Descomente apenas se precisar criar as tabelas sem usar o Alembic
# models.Base.metadata.create_all(bind=engine) 

app = FastAPI()

# Configuração do CORS (está correto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MUDANÇA 2: Inclusão de TODOS os routers da API ---
# Aqui você "conecta" os arquivos de rotas à sua aplicação principal.
# Cada `include_router` faz com que todos os endpoints (@app.get, @app.post, etc.)
# daquele arquivo se tornem ativos na sua API.
app.include_router(auth.router)
app.include_router(match.router) # <-- ESTA LINHA É ESSENCIAL E ESTAVA FALTANDO
app.include_router(chat.router)  # <-- Adicionando para quando for implementar o chat

# --------------------------------------------------------------------
# --- SEÇÃO DO FRONTEND (Servindo os arquivos HTML, CSS, JS) ---
# --------------------------------------------------------------------

# Monta o diretório "static" para que o HTML possa encontrar o CSS e o JS
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Rota para servir a página de login/registro (index.html)
@app.get("/", include_in_schema=False)
async def read_root():
    return FileResponse("frontend/index.html")

# Rota para servir a página de seleção de jogo
@app.get("/game-selector.html", include_in_schema=False)
async def game_selector():
    return FileResponse("frontend/game-selector.html")

# Rota para servir a página de chat
@app.get("/chat/{match_id}", include_in_schema=False)
async def chat_page(match_id: int):
    return FileResponse("frontend/chat.html")

# --- MUDANÇA 3 (A FAZER): Rotas para as novas páginas ---
# Quando você criar as novas telas de "Meus Matches" e "Chat",
# precisará adicionar rotas para elas aqui, seguindo o mesmo padrão.
# Exemplo:
# @app.get("/matches", include_in_schema=False)
# async def my_matches_page():
#     return FileResponse("frontend/matches.html")

# @app.get("/chat/{match_id}", include_in_schema=False)
# async def chat_page(match_id: int):
#     return FileResponse("frontend/chat.html")
# --------------------------------------------------------------------

# Rota de exemplo da API (pode manter ou remover)
@app.get("/api", tags=["Default"])
def api_info():
    return {"message": "Welcome to the API"}