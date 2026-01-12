from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

class Aluno(BaseModel):
    nome: str
    idade: int
    altura: float
    peso: float
    nivel: str
    objetivo: str
    estilo_vida: dict

@app.post("/gerar-treino")
def gerar_treino(aluno: Aluno):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
Você é um professor de educação física experiente.
Crie um plano de treino seguro e personalizado.

Aluno:
Nome: {aluno.nome}
Idade: {aluno.idade}
Altura: {aluno.altura}
Peso: {aluno.peso}
Nível: {aluno.nivel}
Objetivo: {aluno.objetivo}
Estilo de vida: {aluno.estilo_vida}
"""

    resposta = model.generate_content(prompt)
    return {"plano": resposta.text}
