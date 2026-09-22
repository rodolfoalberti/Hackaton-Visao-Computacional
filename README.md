# 🚀 Sistema de Presença Automatizada via Visão Computacional (SIGAA)

> Projeto desenvolvido durante o **Hackathon de Ciência de Dados & Inteligência Artificial**.

Este repositório contém uma solução completa baseada em **Visão Computacional** e **Aprendizado de Máquina** para automatizar o processo de chamada e controle de frequência de alunos em sala de aula, integrando o reconhecimento facial diretamente ao diário eletrônico do SIGAA.

## 📌 Visão Geral do Projeto

O sistema opera capturando imagens via câmera (webcam ou terminal dedicado), reconhecendo a identidade dos alunos cadastrados em tempo real e registrando os eventos de **ENTRADA** e **SAÍDA**. A partir dessas informações, o motor de regras calcula o tempo total de permanência do estudante na aula ($\Delta T$) para determinar automaticamente se o aluno receberá **Presença (1)** ou **Falta (0)**.

## 🛠️ Tecnologias e Dependências

* **Linguagem:** Python 3.8+

* **Visão Computacional & Processamento de Imagem:** `OpenCV` (`cv2`)

* **Reconhecimento Facial:** `DeepFace` (utilizando os modelos `FaceNet` e backend `MTCNN`)

* **Cálculo da Distância de Vetores:** `SciPy` (`scipy.spatial.distance.cosine`)

* **Banco de Dados:** SQLite3 (`sqlite3`)

* **Visualização CLI:** `tabulate`

## 📁 Estrutura de Arquivos

```
├── ingestao.py           # Processa fotos locais e gera embeddings faciais no banco SQLite
├── camera.py            # Executa a captura em tempo real (webcam/multithread) e registra logs
├── motor_frequencia.py   # Processa o cálculo de permanência (Delta T) e gera a pauta final
├── ver_logs.py          # Utilitário CLI para visualizar o histórico detalhado de logs
├── testar_banco.py      # Script auxiliar de teste da base de alunos
├── hackathon_sigaa.db   # Banco de dados SQLite persistente
└── fotos_matricula/     # Diretório base com imagens dos alunos (Ex: MATRICULA_NOME.jpg)

```

## ⚙️ Arquitetura e Módulos do Sistema

### 1. Ingestão e Vetorização de Faces (`ingestao.py`)

* Lê os arquivos do diretório `fotos_matricula/` seguindo o padrão de nomenclatura `MATRICULA_NOME.jpg`.

* Utiliza a biblioteca **DeepFace** com detector **MTCNN** e extração de características com **FaceNet**.

* Salva no banco de dados os vetores numéricos de embedding (armazenados como JSON).

### 2. Reconhecimento em Tempo Real (`camera.py`)

* Opera a captura de vídeo via OpenCV executando o reconhecimento de forma assíncrona (**Threading Paralela**), evitando reduções de FPS no feed de vídeo.

* Aplica métrica de **Distância Cosseno** entre a face capturada e o banco em memória (Limiar de distância $< 0.40$).

* Aplica *Cooldown* de 10 segundos por aluno para evitar gravações redundantes de logs.

* Permite alternating interativa entre modos através das teclas do teclado:

  * `E` / `e`: Alterna terminal para modo **ENTRADA**.

  * `S` / `s`: Alterna terminal para modo **SAÍDA**.

  * `Q` / `q`: Encerra o terminal da câmera.

### 3. Motor de Frequência e Regra de Negócio (`motor_frequencia.py`)

* Calcula a diferença de tempo entre a **Primeira Entrada** e a **Última Saída** registrada ($\Delta T = T_{saida} - T_{entrada}$).

* **Regra do Diário:**

  * Duração padrão da aula: 110 minutos.

  * Exigência mínima: 50% de presença em sala (27.5 minutos).

  * Permite fácil chaveamento para **MODO DEMO** (Exigência de 0.5 minuto para simulação de banca).

### 4. Consulta e Auditoria de Logs (`ver_logs.py` & `testar_banco.py`)

* Exibe o histórico formatado de acessos e estatísticas sumárias de entradas e saídas.

## 🗄️ Esquema do Banco de Dados (`hackathon_sigaa.db`)

O sistema cria e gerencia automaticamente as seguintes tabelas no **SQLite**:

* **`alunos`**: Armazena o cadastro básico e o vetor de características da face (`matricula`, `nome`, `embedding`).

* **`logs_presenca`**: Histórico detalhado dos eventos de acessos capturados na câmera (`id`, `matricula`, `nome`, `tipo`, `timestamp`).

* **`frequencia_sigaa`**: Consolidação das presenças com marcação de entrada, saída e permanência calculada (`matricula`, `nome`, `primeira_entrada`, `ultima_saida`, `permanencia_minutos`, `status_presenca`, `processado_em`).

## 🚀 Como Executar o Projeto

### 1. Instalar as Dependências

```
pip install opencv-python deepface scipy tabulate

```

### 2. Cadastrar Novos Alunos (Ingestão)

Adicione as imagens dos alunos na pasta `fotos_matricula/` nomeadas como `MATRICULA_NOME.jpg` e execute:

```
python ingestao.py

```

### 3. Iniciar o Terminal de Captura

```
python camera.py

```

*(Utilize as teclas `E` e `S` na janela da câmera para alternar entre registro de ENTRADA ou SAÍDA).*

### 4. Consultar os Logs

```
python ver_logs.py

```

### 5. Consolidar o Diário de Frequência do SIGAA

```
python motor_frequencia.py

```

## 👥 Equipe do Projeto

| Integrante | Função | 
 | ----- | ----- | 
| **Rodrigo Junior** | Data Scientist / AI Developer | 
| **Pedro Luiz** | Data Scientist / Developer | 
| **Rodolfo** | Data Analyst / AI Developer | 
| **Bigs** | Developer | Data Analyst |
