
from fastapi import FastAPI

app = FastAPI(
    title="Sistema de Clinica Veterinaria",
    description="API para gerenciamento de animais, microchips e consultas",
    version="1.0.0"
)

@app.get("/")
def inicio():
    return {"mensagem": "API da Clinica Veterinaria funcionando"}
