import sqlite3
from datetime import datetime

# ================= CONFIGURAÇÕES DA REGRA DE NEGÓCIO =================
DURACAO_AULA_MINUTOS = 110
PERCENTUAL_MINIMO = 0.50  # 50% da aula
MINUTOS_NECESSARIOS = DURACAO_AULA_MINUTOS * PERCENTUAL_MINIMO # 27.5 minutos

# DICA PARA O TESTE/APRESENTAÇÃO:
# Se você quiser testar rápido sem esperar 27 minutos, mude MINUTOS_TESTE_DEMO para True.
MODO_DEMO = False
LIMIAR_MINUTOS_DEMO = 0.5  # 1 minuto na sala já dá presença para a banca ver funcionar!
# =====================================================================

def criar_tabela_frequencia(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frequencia_sigaa (
            matricula TEXT PRIMARY KEY,
            nome TEXT,
            primeira_entrada DATETIME,
            ultima_saida DATETIME,
            permanencia_minutos REAL,
            status_presenca INTEGER, -- 1 para Presença, 0 para Falta
            processado_em DATETIME
        )
    ''')
    conn.commit()

def calcular_frequencia():
    conn = sqlite3.connect('hackathon_sigaa.db')
    criar_tabela_frequencia(conn)
    cursor = conn.cursor()

    # Pega todos os alunos matriculados
    cursor.execute("SELECT matricula, nome FROM alunos")
    alunos = cursor.fetchall()

    limiar_tempo = LIMIAR_MINUTOS_DEMO if MODO_DEMO else MINUTOS_NECESSARIOS

    print("=========================================================")
    print(f"      MOTOR DE REGRAS DE NEGÓCIO - CÁLCULO DELTA T       ")
    print(f" Regra: Mínimo de {limiar_tempo:.1f} minutos para Presença (1) ")
    print("=========================================================\n")

    for matricula, nome in alunos:
        # 1. Busca a PRIMEIRA Entrada do aluno
        cursor.execute('''
            SELECT timestamp FROM logs_presenca 
            WHERE matricula = ? AND tipo = 'ENTRADA' 
            ORDER BY timestamp ASC LIMIT 1
        ''', (matricula,))
        res_entrada = cursor.fetchone()

        # 2. Busca a ÚLTIMA Saída do aluno
        cursor.execute('''
            SELECT timestamp FROM logs_presenca 
            WHERE matricula = ? AND tipo = 'SAIDA' 
            ORDER BY timestamp DESC LIMIT 1
        ''', (matricula,))
        res_saida = cursor.fetchone()

        primeira_entrada = res_entrada[0] if res_entrada else None
        ultima_saida = res_saida[0] if res_saida else None
        
        permanencia_minutos = 0.0
        status_presenca = 0  # Padrão: Falta (0)

        # 3. Cálculo do Delta T
        if primeira_entrada and ultima_saida:
            fmt = "%Y-%m-%d %H:%M:%S"
            t_in = datetime.strptime(primeira_entrada, fmt)
            t_out = datetime.strptime(ultima_saida, fmt)

            if t_out > t_in:
                delta_segundos = (t_out - t_in).total_seconds()
                permanencia_minutos = delta_segundos / 60.0

                # 4. Aplicação da Regra
                if permanencia_minutos >= limiar_tempo:
                    status_presenca = 1

        # 5. Atualiza/Insere o resultado na tabela final do SIGAA
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT OR REPLACE INTO frequencia_sigaa 
            (matricula, nome, primeira_entrada, ultima_saida, permanencia_minutos, status_presenca, processado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (matricula, nome, primeira_entrada, ultima_saida, round(permanencia_minutos, 2), status_presenca, agora))

        # Exibe resumo no terminal
        status_txt = "PRESENÇA (1)" if status_presenca == 1 else "FALTA (0)"
        print(f"Aluno: {nome:<15} | Matrícula: {matricula}")
        print(f"  Entrada: {primeira_entrada or 'Sem registro'}")
        print(f"  Saída:   {ultima_saida or 'Sem registro'}")
        print(f"  Permanência: {permanencia_minutos:.2f} min | Status: {status_txt}")
        print("-" * 55)

    conn.commit()
    conn.close()
    print("\nProcessamento do Diário do SIGAA concluído com sucesso!")

if __name__ == "__main__":
    calcular_frequencia()