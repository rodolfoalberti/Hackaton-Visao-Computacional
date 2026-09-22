import os
import sqlite3
import json
from deepface import DeepFace

def criar_banco():
    conn = sqlite3.connect('hackathon_sigaa.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            matricula TEXT PRIMARY KEY,
            nome TEXT,
            embedding TEXT
        )
    ''')
    conn.commit()
    return conn

def processar_fotos(conn):
    pasta_fotos = 'fotos_matricula'
    cursor = conn.cursor()

    print("Iniciando extração de embeddings...")
    
    for arquivo in os.listdir(pasta_fotos):
        if arquivo.endswith(('.jpg', '.jpeg', '.png')):
            caminho_img = os.path.join(pasta_fotos, arquivo)
            
            nome_base = os.path.splitext(arquivo)[0]
            try:
                matricula, nome = nome_base.split('_')
            except ValueError:
                print(f"Erro no nome do arquivo {arquivo}. Use o padrão MATRICULA_NOME.jpg")
                continue

            print(f"Processando: {nome} (Matrícula: {matricula})")
            
            try:
                # O DeepFace extrai as características do rosto. 
                # enforce_detection garante que a foto tem um rosto legível.
                representacao = DeepFace.represent(img_path=caminho_img, model_name="Facenet", detector_backend="mtcnn", enforce_detection=True)                
                # Pega o vetor da primeira pessoa detectada na foto
                embedding = representacao[0]["embedding"]
                
                # Converte a lista de floats para uma string JSON para salvar no SQLite
                embedding_json = json.dumps(embedding)
                
                # Salva no banco (INSERT OR REPLACE atualiza se a matrícula já existir)
                cursor.execute('''
                    INSERT OR REPLACE INTO alunos (matricula, nome, embedding)
                    VALUES (?, ?, ?)
                ''', (matricula, nome, embedding_json))
                
            except ValueError:
                print(f"Nenhum rosto detectado na foto de {nome}. Tire outra foto.")

    conn.commit()
    print("Ingestão concluída com sucesso! Banco atualizado.")

if __name__ == "__main__":
    conexao = criar_banco()
    processar_fotos(conexao)
    conexao.close()