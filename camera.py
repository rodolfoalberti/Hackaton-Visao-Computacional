import cv2
import sqlite3
import json
import time
import threading
from datetime import datetime
from deepface import DeepFace
from scipy.spatial.distance import cosine

# ================= CONFIGURAÇÕES =================
TIPO_CAMERA = "ENTRADA"  # Inicia como Entrada, mas pode mudar apertando as teclas
CAMERA_ID = 0            # 0 é a webcam padrão do notebook
LIMIAR_DISTANCIA = 0.40  # Para o FaceNet, distância cosseno < 0.40 indica a mesma pessoa
# =================================================

def carregar_banco_para_ram():
    conn = sqlite3.connect('hackathon_sigaa.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_presenca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT,
            nome TEXT,
            tipo TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()

    cursor.execute("SELECT matricula, nome, embedding FROM alunos")
    alunos = cursor.fetchall()
    
    banco_em_memoria = []
    for matricula, nome, embedding_str in alunos:
        banco_em_memoria.append({
            "matricula": matricula,
            "nome": nome,
            "embedding": json.loads(embedding_str)
        })
        
    return conn, banco_em_memoria

def registrar_log(conn, matricula, nome):
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO logs_presenca (matricula, nome, tipo, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (matricula, nome, TIPO_CAMERA, agora))
    conn.commit()
    print(f"[{agora}] {TIPO_CAMERA} registrada: {nome}")

# ================= VARIÁVEIS COMPARTILHADAS (THREAD) =================
# Usadas para passar informações do loop principal da câmera para a IA em background
frame_para_analise = None
ia_processando = False
ultimo_resultado_ia = None

def processar_ia_background(banco_alunos):
    """
    Função que roda em paralelo (background) para não travar o FPS da câmera.
    Ela pega uma cópia do frame e tenta achar um rosto.
    """
    global ia_processando, ultimo_resultado_ia, frame_para_analise
    
    try:
        frame = frame_para_analise.copy()
        representacoes = DeepFace.represent(frame, model_name="Facenet", detector_backend="mtcnn", enforce_detection=False)
        
        if len(representacoes) > 0 and representacoes[0].get("face_confidence", 0) > 0:
            vetor_camera = representacoes[0]["embedding"]
            melhor_match = None
            menor_distancia = 1.0 
            
            for aluno in banco_alunos:
                dist = cosine(vetor_camera, aluno["embedding"])
                if dist < menor_distancia:
                    menor_distancia = dist
                    melhor_match = aluno

            if menor_distancia < LIMIAR_DISTANCIA:
                ultimo_resultado_ia = melhor_match  # Passa o dict do aluno
            else:
                ultimo_resultado_ia = "DESCONHECIDO" # Rosto achado, mas não está no banco
        else:
            ultimo_resultado_ia = None # Ninguém na tela
            
    except Exception:
        ultimo_resultado_ia = None
    finally:
        ia_processando = False # Libera para o loop principal mandar um novo frame


def main():
    global TIPO_CAMERA, frame_para_analise, ia_processando, ultimo_resultado_ia
    
    conn, banco_alunos = carregar_banco_para_ram()
    print(f"Banco carregado com {len(banco_alunos)} alunos.")
    print("Controles: [E] Entrada | [S] Saída | [Q] Sair")
    
    cap = cv2.VideoCapture(CAMERA_ID)
    ultimo_registro = {} # Regra de cooldown

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 1. Tenta mandar um frame para a IA analisar, se ela estiver livre
        if not ia_processando:
            frame_para_analise = frame.copy()
            ia_processando = True
            # Inicia a IA em uma thread paralela
            threading.Thread(target=processar_ia_background, args=(banco_alunos,), daemon=True).start()
        
        # 2. Desenha na tela o ÚLTIMO resultado que a IA conseguiu descobrir
        if isinstance(ultimo_resultado_ia, dict):
            nome_detectado = ultimo_resultado_ia["nome"]
            matricula_detectada = ultimo_resultado_ia["matricula"]
            
            # Cooldown de 10 segundos
            tempo_atual = time.time()
            tempo_ultimo = ultimo_registro.get(matricula_detectada, 0)
            
            if (tempo_atual - tempo_ultimo) > 10:
                # Importante: o SQLite faz o registro de log na Thread principal para evitar crash de DB
                registrar_log(conn, matricula_detectada, nome_detectado)
                ultimo_registro[matricula_detectada] = tempo_atual

            # Desenha verde se reconheceu
            cv2.putText(frame, f"ALUNO: {nome_detectado}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
        elif ultimo_resultado_ia == "DESCONHECIDO":
            # Desenha vermelho se não for aluno
            cv2.putText(frame, "ALUNO DESCONHECIDO", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # 3. Cabeçalho HUD sempre ativo informando o modo
        cor_cabecalho = (0, 255, 255) if TIPO_CAMERA == "ENTRADA" else (255, 165, 0)
        cv2.putText(frame, f"TERMINAL: {TIPO_CAMERA}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_cabecalho, 2)
        cv2.putText(frame, "[E] Entrada | [S] Saida", (30, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Hackathon - Sistema SIGAA", frame)
        
        # 4. Captura do Teclado
        key = cv2.waitKey(1) & 0xFF
        
        if key in [ord('q'), ord('Q')]: # Sair
            break
        elif key in [ord('e'), ord('E')]: # Mudar para Entrada
            TIPO_CAMERA = "ENTRADA"
            print("==> MODO ALTERADO PARA: ENTRADA")
        elif key in [ord('s'), ord('S')]: # Mudar para Saída
            TIPO_CAMERA = "SAIDA"
            print("==> MODO ALTERADO PARA: SAÍDA")

    cap.release()
    cv2.destroyAllWindows()
    conn.close()

if __name__ == "__main__":
    main()