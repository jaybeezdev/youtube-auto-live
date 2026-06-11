# ▷ Youtube Auto Live

Tive a ideia de desenvolver este projeto para a TV Pernambuco a fim de evitar que o canal do YouTube tomasse strikes por exibir conteúdo de terceiros e para evitar esquecimento na hora de iniciar a live diária do jornal "Pernambuco Hoje". Trata-se de um gerenciador automatizado para transmissões ao vivo com autenticador no YouTube, integrado com o Agendador de Tarefas do Windows para permitir automação total sem a necessidade de intervenção manual diária.

*OBS: Esta versão inicial pode apresentar alguns bugs, pois está em fase de testes. Porém, já é 100% funcional para o propósito do projeto. Estão em desenvolvimento condicionais para entradas de informações, tratamento de exceções e melhorias operacionais na interface gráfica.*

---

## 🚀 Funcionalidades
- **Automação Completa**: Inicia e encerra transmissões nos horários definidos diretamente via Agendador de Tarefas.
- **Configuração via Interface**: Interface gráfica moderna e intuitiva para definir título, descrição, visibilidade, miniatura e horários de início e fim.
- **Modo Background Inteligente**: O agendamento roda de forma 100% invisível no Windows, sem abrir janelas pretas de prompt indesejadas (via `pythonw.exe` ou em modo congelado `.exe`).
- **Resiliência de Thumbnail**: Tenta enviar a capa personalizada e, em caso de limites de cota da API, mantém a configuração padrão do YouTube para não interromper o fluxo da live.
- **Pré-criação de Eventos**: As lives são pré-configuradas no YouTube Studio, garantindo que o sinal esteja pronto no momento exato do início.

---

## 🛠️ Como Configurar e Executar (Ambiente de Desenvolvimento)

### 1. Requisitos do Sistema
- **Python 3.11 ou 3.12** instalado.
  - ⚠️ **MUITO IMPORTANTE**: Durante a instalação do Python no Windows, certifique-se de marcar a caixinha **"Add python.exe to PATH"** na primeira tela do instalador:
   
  <img width="656" height="415" alt="python-path" src="https://github.com/user-attachments/assets/22190065-8cb5-48fa-b5e3-a0c50dc738eb" />
    
  - *Dica:* Se o Windows insistir em abrir a Microsoft Store ao digitar `python`, vá em *Configurações > Aplicativos > Aliases de execução do aplicativo* e desative os seletores do Python.


### 2. Configuração de Credenciais do Google
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto e habilite a API **YouTube Data API v3**.
3. Vá em **APIs e Serviços > Credenciais** e crie um **ID do cliente OAuth 2.0** (selecione o tipo "Aplicativo de Desktop").
4. Faça o download do arquivo JSON gerado.
5. Renomeie o arquivo baixado para **`client_secret.json`** (remova o código client_id do nome do arquivo) e cole-o obrigatoriamente na raiz deste projeto.

### 3. Instalação e Preparação do Ambiente (`venv`)
Como a pasta `venv` está listada no `.gitignore` por boas práticas de portabilidade, você deve criar um ambiente isolado para esta máquina.
Abra o terminal na pasta do projeto (`SHIFT + Botão direito do mouse > Abrir janela do PowerShell aqui`) e dê o seguinte comando na janela do PowerShell para instalar as dependências necessárias para o funcionamento do programa:

`pip install -r requirements.txt`

### 4. Primeira Execução
Para abrir a aplicação, digite o seguinte comando:

`.\venv\Scripts\python app.py`

Ao iniciar o aplicativo pela primeira vez, uma janela do navegador abrirá solicitando que você autorize o acesso à sua conta do YouTube (caso não abra, clique em `🔑 Fazer Login`). Após a autorização, um arquivo token.json será gerado automaticamente.

## ⚠️ IMPORTANTE:
Nunca compartilhe os arquivos token.json ou client_secret.json. Eles contêm as chaves de acesso à sua conta.


## 📁 Estrutura de Segurança
Este projeto utiliza um arquivo .gitignore para garantir que arquivos sensíveis nunca sejam enviados ao GitHub. Certifique-se de não remover as entradas de .json do arquivo .gitignore.

