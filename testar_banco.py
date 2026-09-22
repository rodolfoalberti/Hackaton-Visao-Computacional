import sqlite3
import json

conn = sqlite3.connect('hackathon_sigaa.db')
cursor = conn.cursor()
cursor.execute("SELECT matricula, nome, embedding FROM alunos")

alunos = cursor.fetchall()
print(f"Total de alunos cadastrados: {len(alunos)}\n")

for matricula, nome, embedding_str in alunos:
    embedding = json.loads(embedding_str)
    print(f"Aluno: {nome} | Matrícula: {matricula} | Tamanho do Vetor: {len(embedding)} dimensões")
    
conn.close()