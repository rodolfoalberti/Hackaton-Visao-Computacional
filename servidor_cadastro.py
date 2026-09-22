import os
import json
import base64
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deepface import DeepFace

app = Flask(__name__)
CORS(app)  # Permite requisições vindas do navegador

PASTA_FOTOS = "fotos_matricula"
os.makedirs(PASTA_FOTOS, exist_ok=True)

def inicializar_banco():
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
    conn.close()

# Rota para servir as imagens salvas na pasta fotos_matricula/
@app.route('/fotos/<path:filename>')
def servir_foto(filename):
    return send_from_directory(PASTA_FOTOS, filename)

# Rota para listar os alunos e fotos já cadastrados no banco/pasta
@app.route('/api/alunos', methods=['GET'])
def listar_alunos():
    try:
        conn = sqlite3.connect('hackathon_sigaa.db')
        cursor = conn.cursor()
        cursor.execute("SELECT matricula, nome, embedding FROM alunos")
        registros = cursor.fetchall()
        conn.close()

        alunos = []
        for matricula, nome, embedding_str in registros:
            nome_arquivo = f"{matricula}_{nome}.jpg"
            caminho_foto = os.path.join(PASTA_FOTOS, nome_arquivo)
            
            # Se o arquivo existe na pasta fotos_matricula, gera a URL de exibição
            foto_url = f"http://localhost:5000/fotos/{nome_arquivo}" if os.path.exists(caminho_foto) else ""
            
            alunos.append({
                "id": matricula,
                "matricula": matricula,
                "nome": nome,
                "fileName": nome_arquivo,
                "photoUrl": foto_url,
                "embedding": json.loads(embedding_str) if embedding_str else []
            })

        return jsonify(alunos), 200
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/cadastrar', methods=['POST'])
def cadastrar_aluno():
    try:
        dados = request.json
        matricula = dados.get('matricula')
        nome = dados.get('nome')
        imagem_b64 = dados.get('imagem_base64')

        if not matricula or not nome or not imagem_b64:
            return jsonify({"status": "erro", "mensagem": "Dados incompletos!"}), 400

        # Remove o cabeçalho 'data:image/jpeg;base64,' se existir
        if ',' in imagem_b64:
            imagem_b64 = imagem_b64.split(',')[1]

        # 1. Salva o arquivo de imagem formatado em fotos_matricula/
        caminho_foto = os.path.join(PASTA_FOTOS, f"{matricula}_{nome}.jpg")
        with open(caminho_foto, "wb") as f:
            f.write(base64.b64decode(imagem_b64))

        # 2. Roda a IA para extrair o embedding (Fase 1)
        # No arquivo servidor_cadastro.py, modifique a chamada do DeepFace:
        representacao = DeepFace.represent(
            img_path=caminho_foto, 
            model_name="Facenet", 
            detector_backend="mtcnn",  # Alterado para mtcnn
            enforce_detection=False
        )
        embedding = representacao[0]["embedding"]

        # 3. Insere ou atualiza no SQLite
        conn = sqlite3.connect('hackathon_sigaa.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO alunos (matricula, nome, embedding)
            VALUES (?, ?, ?)
        ''', (matricula, nome, json.dumps(embedding)))
        conn.commit()
        conn.close()

        print(f"✅ Cadastrado com sucesso: {nome} ({matricula})")
        return jsonify({"status": "sucesso", "mensagem": f"Aluno {nome} cadastrado com sucesso!"}), 200

    except Exception as e:
        print(f"❌ Erro no cadastro: {str(e)}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    inicializar_banco()
    print("🚀 Servidor de Ingestão rodando em http://localhost:5000")
    app.run(port=5000, debug=True)