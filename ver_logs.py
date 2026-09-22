import sqlite3
from tabulate import tabulate

DB_NAME = 'hackathon_sigaa.db'

def consultar_logs():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Consulta os registros na tabela logs_presenca
        query = '''
            SELECT 
                id,
                matricula,
                nome,
                tipo,
                timestamp
            FROM logs_presenca
            ORDER BY timestamp DESC
        '''
        
        cursor.execute(query)
        registros = cursor.fetchall()
        conn.close()

        if not registros:
            print("\n[!] Nenhum registro de presença encontrado no banco de dados.\n")
            return

        # Estatísticas rápidas para apresentação
        total_entradas = sum(1 for r in registros if str(r[3]).upper() == 'ENTRADA')
        total_saidas = sum(1 for r in registros if str(r[3]).upper() == 'SAIDA')

        headers = ["ID", "Matrícula", "Nome do Aluno", "Evento", "Data/Hora"]
        
        print("\n" + "=" * 70)
        print("          HISTÓRICO DE LOGS DE PRESENÇA - SIGAA")
        print("=" * 70)
        print(tabulate(registros, headers=headers, tablefmt="grid"))
        print(f"\n📊 RESUMO DE ACESSOS:")
        print(f"   • Total de Registros: {len(registros)}")
        print(f"   • Entradas: {total_entradas}")
        print(f"   • Saídas:   {total_saidas}\n")

    except sqlite3.OperationalError:
        print("\n[Aviso] Tabela 'logs_presenca' ainda não foi criada.")
        print("Execute o script da câmera ao menos uma vez para inicializar o banco.\n")
    except Exception as e:
        print(f"\n[Erro ao ler banco de dados]: {e}\n")

if __name__ == '__main__':
    consultar_logs()