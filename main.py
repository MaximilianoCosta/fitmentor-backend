from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import random
from google import genai

app = FastAPI()

API_KEY = os.getenv("GEMINI_API_KEY")

# =========================
# MODELOS
# =========================

class Aluno(BaseModel):
    nome: str
    idade: int
    altura: float
    peso: float
    nivel: str            # iniciante | intermediario | avancado
    objetivo: str         # Emagrecimento | Hipertrofia | Condicionamento
    estilo_vida: dict

# =========================
# MAPA DE EXERCÍCIOS (IDS)
# =========================

EXERCISE_MAP = {
    "pernas": {
        "iniciante": [
            "leg-press",
            "afundo",
            "cadeira-extensora",
            "mesa-flexora"
        ],
        "intermediario": [
            "agachamento-livre",
            "stiff",
            "afundo",
            "leg-press"
        ],
        "avancado": [
            "agachamento-livre",
            "stiff",
            "afundo"
        ]
    },
    "costas": {
        "iniciante": [
            "puxada-frontal",
            "remada-baixa"
        ],
        "intermediario": [
            "puxada-frontal",
            "remada-curvada",
            "remada-baixa"
        ],
        "avancado": [
            "barra-fixa",
            "remada-curvada"
        ]
    },
    "peito": {
        "iniciante": [
            "crucifixo",
            "cross-over"
        ],
        "intermediario": [
            "supino-reto",
            "supino-inclinado",
            "crucifixo"
        ],
        "avancado": [
            "supino-reto",
            "supino-inclinado"
        ]
    },
    "ombros": {
        "iniciante": [
            "elevacao-lateral",
            "elevacao-frontal"
        ],
        "intermediario": [
            "desenvolvimento-halteres",
            "elevacao-lateral"
        ],
        "avancado": [
            "desenvolvimento-halteres"
        ]
    },
    "bracos": {
        "iniciante": [
            "rosca-direta",
            "triceps-corda"
        ],
        "intermediario": [
            "rosca-alternada",
            "triceps-testa"
        ],
        "avancado": [
            "rosca-martelo",
            "mergulho-banco"
        ]
    },
    "core": {
        "iniciante": [
            "abdominal-crunch",
            "prancha"
        ],
        "intermediario": [
            "prancha",
            "abdominal-obliquo"
        ],
        "avancado": [
            "prancha"
        ]
    }
}

OBJETIVO_GRUPOS = {
    "Emagrecimento": ["pernas", "costas", "peito", "core"],
    "Hipertrofia": ["pernas", "peito", "costas", "ombros", "bracos"],
    "Condicionamento": ["pernas", "core", "costas"]
}

# =========================
# FUNÇÕES AUXILIARES
# =========================

def selecionar_exercicios(grupos, nivel, quantidade=6):
    selecionados = []

    for grupo in grupos:
        exercicios = EXERCISE_MAP.get(grupo, {}).get(nivel, [])
        random.shuffle(exercicios)
        selecionados.extend(exercicios)

    # remove duplicados mantendo ordem
    selecionados = list(dict.fromkeys(selecionados))

    return selecionados[:quantidade]

# =========================
# ROTAS
# =========================

@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "FitMentor backend rodando",
        "endpoints": ["/docs", "/gerar-treino"]
    }

@app.post("/gerar-treino")
def gerar_treino(aluno: Aluno):

    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY não configurada no Render."
        )

    try:
        client = genai.Client(api_key=API_KEY)

        nivel = aluno.nivel.lower()
        grupos = OBJETIVO_GRUPOS.get(
            aluno.objetivo,
            ["pernas", "costas", "core"]
        )

        ids_exercicios = selecionar_exercicios(
            grupos=grupos,
            nivel=nivel,
            quantidade=6
        )

        if not ids_exercicios:
            raise HTTPException(
                status_code=400,
                detail="Nenhum exercício encontrado para este perfil."
            )

        prompt = f"""
Você é um professor de educação física experiente.

REGRAS OBRIGATÓRIAS:
- Use SOMENTE os exercícios desta lista de IDs:
{ids_exercicios}
- NÃO invente exercícios
- NÃO use nomes fora da lista
- Retorne APENAS JSON válido
- Não inclua texto fora do JSON

FORMATO EXATO:
{{
  "treino": [
    {{
      "exercicio_id": "id_da_lista",
      "series": 3,
      "repeticoes": "10-12",
      "descanso_segundos": 60,
      "observacao": "dica técnica curta"
    }}
  ]
}}

DADOS DO ALUNO:
Idade: {aluno.idade}
Altura: {aluno.altura}
Peso: {aluno.peso}
Nível: {aluno.nivel}
Objetivo: {aluno.objetivo}
Estilo de vida: {aluno.estilo_vida}
"""

        resp = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        texto = getattr(resp, "text", None)

        if not texto:
            raise HTTPException(
                status_code=500,
                detail="Modelo não retornou resposta."
            )

        return {
            "exercicios_permitidos": ids_exercicios,
            "resultado": texto
        }

    except HTTPException:
        raise
    except Exception as e:
        print("ERRO AO GERAR TREINO:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
