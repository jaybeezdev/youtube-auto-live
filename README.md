# Gerenciador de Lives — TV Pernambuco

Tive a ideia de desenvolver este projeto para a TV Pernambuco (emissora em que atualmente trabalho) a fim de evitar que o canal do Youtube tomasse strikes por exibir conteúdo de terceiros e para evitar esquecimento na hora de iniciar a live diária do jornal "Pernambuco Hoje". Trata-se de um gerenciador automatizado para transmissões ao vivo com autenticador no Youtube, integrado com o Agendador de Tarefas do Windows para permitir automação total sem a necessidade de intervenção manual diária.

## 🚀 Funcionalidades
- **Automação Completa**: Inicia e encerra transmissões nos horários definidos.
- **Configuração via Interface**: Interface gráfica intuitiva para definir título, descrição, visibilidade e horários.
- **Modo Background**: O agendamento roda silenciosamente no Windows, sem janelas indesejadas (via `pythonw.exe`).
- **Resiliência de Thumbnail**: Tenta enviar a capa personalizada e, em caso de limites de cota da API, mantém a configuração padrão do YouTube para não interromper a live.
- **Pré-criação de Eventos**: As lives são pré-configuradas no YouTube Studio, garantindo que o sinal esteja pronto no momento do início.

## 🛠️ Como Configurar

### 1. Requisitos
- Python 3.x instalado.
- Projeto criado no [Google Cloud Console](https://console.cloud.google.com/).
- API **YouTube Data API v3** habilitada no projeto.

### 2. Credenciais
1. No console do Google Cloud, vá em **APIs e Serviços > Credenciais**.
2. Crie um **ID do cliente OAuth 2.0** (selecione "Aplicativo de Desktop").
3. Faça o download do arquivo JSON.
4. Renomeie o arquivo baixado para `client_secret.json` e coloque-o na pasta raiz deste projeto.

### 3. Instalação
Abra o terminal na pasta do projeto e instale as dependências:

pip install -r requirements.txt

### 4. Primeira Execução
Ao iniciar o aplicativo pela primeira vez, uma janela do navegador abrirá solicitando que você autorize o acesso à sua conta do YouTube. Após a autorização, um arquivo token.json será gerado automaticamente.

## ⚠️ IMPORTANTE:
Nunca compartilhe os arquivos token.json ou client_secret.json. Eles contêm as chaves de acesso à sua conta.


## 📁 Estrutura de Segurança
Este projeto utiliza um arquivo .gitignore para garantir que arquivos sensíveis nunca sejam enviados ao GitHub. Certifique-se de não remover as entradas de .json do arquivo .gitignore.

### Próximos passos recomendados:
1.  **requirements.txt**: Lembre-se de gerar o arquivo com as dependências do seu projeto (usando `pip freeze > requirements.txt`) para que o comando de instalação no README funcione corretamente para quem baixar.
2.  **gitignore**: Caso ainda não tenha, crie o arquivo `.gitignore` na raiz com o conteúdo abaixo para garantir que você não envie credenciais por engano:
    
    token.json
    client_secret.json
    venv/
    __pycache__/
    .env
    
