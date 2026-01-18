from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
import os
from google import genai

app = FastAPI()

API_KEY = os.getenv("GEMINI_API_KEY")

# =========================
# CATÁLOGO DE EXERCÍCIOS
# (Você pode ir aumentando depois)
# IMPORTANTE: video_url pode ser Cloudinary (recomendado)
# =========================
EXERCISES: List[Dict[str, Any]] = [
    # Peito
    {"id": "supino-reto", "nome": "Supino reto", "grupo": "peito", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia","Força"], "video_url": ""},
    {"id": "supino-inclinado", "nome": "Supino inclinado", "grupo": "peito", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia"], "video_url": ""},
    {"id": "flexao", "nome": "Flexão de braço", "grupo": "peito", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Emagrecimento","Resistência","Hipertrofia"], "video_url": ""},

    # Costas
    {"id": "puxada-frontal", "nome": "Puxada frontal", "grupo": "costas", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia","Força"], "video_url": ""},
    {"id": "remada-curvada", "nome": "Remada curvada", "grupo": "costas", "nivel": ["Intermediário","Avançado"], "objetivos": ["Hipertrofia","Força"], "video_url": ""},
    {"id": "remada-sentada", "nome": "Remada sentada", "grupo": "costas", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia"], "video_url": ""},

    # Pernas
    {"id": "agachamento", "nome": "Agachamento", "grupo": "pernas", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Emagrecimento","Hipertrofia","Força"], "video_url": ""},
    {"id": "leg-press", "nome": "Leg press", "grupo": "pernas", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia","Força"], "video_url": ""},
    {"id": "stiff", "nome": "Stiff / Terra romeno", "grupo": "pernas", "nivel": ["Intermediário","Avançado"], "objetivos": ["Hipertrofia","Força"], "video_url": ""},

    # Ombros
    {"id": "desenvolvimento", "nome": "Desenvolvimento (ombros)", "grupo": "ombros", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia","Força"], "video_url": ""},
    {"id": "elevacao-lateral", "nome": "Elevação lateral", "grupo": "ombros", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia"], "video_url": ""},

    # Bíceps
    {"id": "rosca-direta", "nome": "Rosca direta", "grupo": "biceps", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia"], "video_url": ""},
    {"id": "rosca-alternada", "nome": "Rosca alternada", "grupo": "biceps", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia"], "video_url": ""},

    # Tríceps
    {"id": "triceps-corda", "nome": "Tríceps na corda", "grupo": "triceps", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Hipertrofia"], "video_url": ""},
    {"id": "triceps-testa", "nome": "Tríceps testa", "grupo": "triceps", "nivel": ["Intermediário","Avançado"], "objetivos": ["Hipertrofia"], "video_url": ""},

    # Core
    {"id": "prancha", "nome": "Prancha", "grupo": "core", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Emagrecimento","Resistência","Hipertrofia"], "video_url": ""},
    {"id": "abdominal-bicicleta", "nome": "Abdominal bicicleta", "grupo": "core", "nivel": ["Iniciante","Intermediário","Avançado"], "objetivos": ["Emagrecimento","Resistência"], "video_url": ""},
]


# =========================
# MODEL
# =========================
class Aluno(BaseModel):
    nome: str
    idade: int
    altura: float
    peso: float
    nivel: str
    # aceita string OU lista (porque seu app virou múltipla escolha)
    objetivo: Union[str, List[str]]
    estilo_vida: Dict[str, Any]


def _normalize_objetivo(obj: Union[str, List[str]]) -> List[str]:
    if isinstance(obj, list):
        return [str(x).strip() for x in obj if str(x).strip()]
    s = str(obj).strip()
    return [s] if s else []


def filtrar_exercicios(nivel: str, objetivos: List[str]) -> List[Dict[str, Any]]:
    nivel = (nivel or "").strip()
    objetivos = [o.strip() for o in objetivos if o.strip()]

    # 1) tenta bater NIVEL + OBJETIVO
    candidatos = [
        e for e in EXERCISES
        if nivel in e.get("nivel", []) and (not objetivos or any(o in e.get("objetivos", []) for o in objetivos))
    ]

    # 2) se não achou, tenta só NIVEL
    if not candidatos:
        candidatos = [e for e in EXERCISES if nivel in e.get("nivel", [])]

    # 3) se ainda não achou, usa tudo (fallback final)
    if not candidatos:
        candidatos = EXERCISES[:]

    return candidatos


@app.get("/")
def home():
    return {"status": "ok", "message": "FitMentor backend rodando. Use /docs e /models"}


@app.get("/models")
def listar_models():
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY não configurada.")
    try:
        client = genai.Client(api_key=API_KEY)
        modelos = []
        for m in client.models.list():
            modelos.append(getattr(m, "name", str(m)))
        return {"models": modelos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gerar-treino")
def gerar_treino(aluno: Aluno):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY não configurada no Render.")

    try:
        objetivos = _normalize_objetivo(aluno.objetivo)
        exercicios_ok = filtrar_exercicios(aluno.nivel, objetivos)

        # pega uma seleção simples (você vai sofisticar depois)
        # aqui montamos um full-body básico com 6–8 exercícios
        base = exercicios_ok[:8]

        # prompt já inclui lista de exercícios para a IA "escolher"
        lista_ex = "\n".join([f"- {e['nome']} (grupo: {e['grupo']}, id: {e['id']})" for e in base])

        client = genai.Client(api_key=API_KEY)

        prompt = f"""
Você é um professor de educação física experiente.
Crie um plano de treino SEGURO, OBJETIVO e PERSONALIZADO.

Aluno:
Nome: {aluno.nome}
Idade: {aluno.idade}
Altura: {aluno.altura} m
Peso: {aluno.peso} kg
Nível: {aluno.nivel}
Objetivo(s): {", ".join(objetivos) if objetivos else "Não informado"}

Estilo de vida e saúde (considerar intensidade e escolhas):
{aluno.estilo_vida}

Use APENAS exercícios desta lista (se precisar, repita algum):
{lista_ex}

Regras:
- Divida em aquecimento, parte principal e alongamento.
- Na parte principal, traga 6 a 8 exercícios (nome + séries + reps + descanso).
- Sugira progressão semanal simples.
- Formato em tópicos, bem organizado.
"""

        resp = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        texto = getattr(resp, "text", None) or "Sem resposta do modelo."
        return {"plano": texto, "exercicios_sugeridos": base}

    except Exception as e:
        print("ERRO AO GERAR TREINO:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
