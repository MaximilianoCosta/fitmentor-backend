from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

from google import genai

app = FastAPI()

API_KEY = os.getenv("GEMINI_API_KEY")

class Aluno(BaseModel):
    nome: str
    idade: int
    altura: float
    peso: float
    nivel: str
    objetivo: str
    estilo_vida: dict

@app.get("/")
def home():
    return {"status": "ok", "message": "FitMentor backend rodando. Use /docs"}

@app.post("/gerar-treino")
def gerar_treino(aluno: Aluno):
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY não configurada no Render (Environment).",
        )

    try:
        client = genai.Client(api_key=API_KEY)

        prompt = f"""
Você é um professor de educação física experiente.
Crie um plano de treino seguro, objetivo e personalizado.

Aluno:
Nome: {aluno.nome}
Idade: {aluno.idade}
Altura: {aluno.altura} m
Peso: {aluno.peso} kg
Nível: {aluno.nivel}
Objetivo: {aluno.objetivo}

Estilo de vida e saúde (considerar na intensidade e escolhas):
{aluno.estilo_vida}

Regras:
- Priorize segurança.
- Dê sugestões progressivas.
- Divida em aquecimento, parte principal e alongamento.
- Formato em tópicos, bem organizado.
"""

        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        texto = getattr(resp, "text", None) or "Sem resposta do modelo."
        return {"plano": texto}

    except Exception as e:
        print("ERRO AO GERAR TREINO:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
