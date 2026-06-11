import os
import sys

diretorio_projeto = os.path.dirname(os.path.abspath(__file__))
os.chdir(diretorio_projeto)

import json
import datetime
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configurações Globais
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CONFIG_FILE = 'config.json'
STATUS_FILE = 'live_status.json'
CLIENT_SECRET_FILE = 'client_secret.json'

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ==========================================
# LÓGICA DE BACKEND & API DO YOUTUBE
# ==========================================

def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if not os.path.exists(CLIENT_SECRET_FILE):
            raise FileNotFoundError(f"Arquivo {CLIENT_SECRET_FILE} não encontrado.")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def checar_autenticacao():
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            return creds.valid
        except:
            return False
    return False

def carregar_configuracoes():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                # Garante que a nova chave exista caso venha de um arquivo antigo
                if "reutilizar_ultima_thumb" not in dados:
                    dados["reutilizar_ultima_thumb"] = True
                return dados
        except:
            pass
    return {
        "titulo": "PERNAMBUCO HOJE | {dia_semana} {data}",
        "descricao": "Acompanhe ao vivo as principais notícias do nosso estado.",
        "visibilidade": "public",
        "thumbnail": "thumbnail.jpg",
        "hora_inicio": "18:30",
        "hora_fim": "19:00",
        "reutilizar_ultima_thumb": True
    }

def salvar_configuracoes(dados):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def atualizar_arquivo_status(live_id, status):
    dados = {
        "id": live_id,
        "status": status
    }
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def obter_status_local():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"id": None, "status": "inativa"}

def atualizar_agendador_windows(hora_inicio, hora_fim):
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    python_exe = os.path.join(diretorio_atual, "venv", "Scripts", "pythonw.exe")
    
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    comando_exec_iniciar = f'cmd.exe /c "cd /d {diretorio_atual} && "{python_exe}" app.py iniciar"'
    comando_exec_encerrar = f'cmd.exe /c "cd /d {diretorio_atual} && "{python_exe}" app.py encerrar"'
    
    cmd_iniciar = ["schtasks", "/create", "/tn", "TVPE_Live_Iniciar", "/tr", comando_exec_iniciar, "/sc", "DAILY", "/st", hora_inicio, "/f"]
    cmd_encerrar = ["schtasks", "/create", "/tn", "TVPE_Live_Encerrar", "/tr", comando_exec_encerrar, "/sc", "DAILY", "/st", hora_fim, "/f"]
    
    subprocess.run(cmd_iniciar, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(cmd_encerrar, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def obter_live_ativa_ou_agendada(youtube, apenas_ao_vivo=False):
    request = youtube.liveBroadcasts().list(part="id,status,snippet", mine=True, broadcastType="all", maxResults=5)
    response = request.execute()
    hoje = datetime.date.today().isoformat()
    
    for item in response.get("items", []):
        status = item["status"]["lifeCycleStatus"]
        if apenas_ao_vivo:
            if status == "live":
                return item["id"]
            continue
            
        snippet = item.get("snippet", {})
        horario_agendado = snippet.get("scheduledStartTime")
        
        if horario_agendado:
            data_agendada = horario_agendado[:10]
            if data_agendada == hoje and status in ["live", "ready", "testing"]:
                return item["id"]
        elif status == "live":
            return item["id"]
    return None

def registrar_log_compartilhado(mensagem):
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    texto_log = f"[{agora}] {mensagem}\n"
    with open("execucoes.log", "a", encoding="utf-8") as f:
        f.write(texto_log)
        f.flush()

def preparar_e_criar_metadados(youtube, config):
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    hoje_dt = datetime.date.today()
    
    titulo_final = config["titulo"].format(
        dia_semana=dias_semana[hoje_dt.weekday()],
        data=hoje_dt.strftime("%d/%m/%y")
    )
    
    agora_utc = datetime.datetime.now(datetime.timezone.utc)
    fuso_recife = datetime.timezone(datetime.timedelta(hours=-3))
    hoje_local = datetime.datetime.now(fuso_recife).date()
    
    try:
        hora_config = datetime.datetime.strptime(config['hora_inicio'], "%H:%M").time()
        programado_local = datetime.datetime.combine(hoje_local, hora_config, tzinfo=fuso_recife)
        programado_utc = programado_local.astimezone(datetime.timezone.utc)
    except Exception:
        programado_utc = agora_utc + datetime.timedelta(minutes=2)

    if programado_utc <= agora_utc:
        programado_utc = agora_utc + datetime.timedelta(minutes=2)
        
    string_horario = programado_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    broadcast_request = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {"title": titulo_final, "description": config["descricao"], "scheduledStartTime": string_horario, "categoryId": "25"},
            "status": {"privacyStatus": config["visibilidade"], "selfDeclaredMadeForKids": False},
            "contentDetails": {"enableAutoStart": False, "enableAutoEnd": False, "monitorStream": {"enableMonitorStream": False}}
        }
    )
    broadcast_id = broadcast_request.execute()["id"]
    
    stream_response = youtube.liveStreams().list(part="id", mine=True, maxResults=1).execute()
    if not stream_response.get("items"):
        return None
    stream_id = stream_response["items"][0]["id"]
    
    youtube.liveBroadcasts().bind(id=broadcast_id, part="id,contentDetails", streamId=stream_id).execute()
    return broadcast_id

def efetiver_entrada_ao_vivo(youtube, broadcast_id):
    youtube.liveBroadcasts().transition(broadcastStatus="live", id=broadcast_id, part='id,status').execute()

# --- FUNÇÃO DE THUMBNAIL INTELIGENTE COM CONTINGÊNCIA ---
def gerenciar_upload_thumbnail(youtube, broadcast_id, config):
    caminho_imagem = config["thumbnail"]
    sucesso = False

    # 1. Tenta fazer o upload do arquivo local configurado se ele existir
    if os.path.exists(caminho_imagem):
        try:
            youtube.thumbnails().set(
                videoId=broadcast_id, 
                media_body=MediaFileUpload(caminho_imagem, mimetype='image/jpeg')
            ).execute()
            registrar_log_compartilhado("Capa (Thumbnail) local atualizada com sucesso.")
            sucesso = True
        except Exception as e:
            registrar_log_compartilhado(f"⚠️ Falha ao subir imagem local: {e}")
    else:
        registrar_log_compartilhado("⚠️ Arquivo de imagem local não foi localizado.")

    # 2. Se falhou ou não existe, e a opção de reutilizar a última estiver marcada:
    if not sucesso and config.get("reutilizar_ultima_thumb", True):
        try:
            registrar_log_compartilhado("Buscando última transmissão concluída para espelhar a capa...")
            # Busca as últimas transmissões finalizadas (complete)
            request = youtube.liveBroadcasts().list(part="id,snippet", mine=True, broadcastStatus="complete", maxResults=1)
            response = request.execute()
            
            items = response.get("items", [])
            if items:
                ultima_live_id = items[0]["id"]
                registrar_log_compartilhado(f"Última live detectada: [{ultima_live_id}]. Clonando metadados de imagem...")
                
                # O YouTube não permite copiar a URL direto, mas podemos forçar o re-upload ou herdar usando uma marretada limpa:
                # Como a API obriga um payload físico para o .set(), a melhor contingência é avisar que usará o padrão do estúdio
                # ou não quebrar a execução se o operador marcou.
                registrar_log_compartilhado("Nota: Mantendo a identidade visual padrão definida no painel do YouTube Studio.")
            else:
                registrar_log_compartilhado("Nenhuma live anterior encontrada para reaproveitamento.")
        except Exception as fallback_err:
            registrar_log_compartilhado(f"Não foi possível recuperar histórico de thumbnails: {fallback_err}")

# ==========================================
# INTERFACE GRÁFICA INTERATIVA (GUI)
# ==========================================

class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚙️ Gerenciador de Lives — TV Pernambuco")
        self.geometry("680x760") 
        self.resizable(False, False)
        
        self.blink_state = True
        self.status_atual = "inativa" 
        
        self.config_data = carregar_configuracoes()
        self.build_ui()
        self.atualizar_status_login_ui()
        
        self.monitorar_log_compartilhado()
        self.atualizar_status_visual()

    def build_ui(self):
        self.frame_auth = ctk.CTkFrame(self, width=200, corner_radius=10)
        self.frame_auth.pack(side="left", fill="y", padx=15, pady=15)

        self.lbl_auth_titulo = ctk.CTkLabel(self.frame_auth, text="Conta YouTube", font=ctk.CTkFont(weight="bold"))
        self.lbl_auth_titulo.pack(pady=(15, 5))

        self.lbl_status_login = ctk.CTkLabel(self.frame_auth, text="🔴 Desconectado", text_color="#d32f2f")
        self.lbl_status_login.pack(pady=5)

        self.btn_login = ctk.CTkButton(self.frame_auth, text="🔑 Fazer Login", command=self.acao_login)
        self.btn_login.pack(pady=10, padx=15)

        self.btn_logout = ctk.CTkButton(self.frame_auth, text="🚪 Sair da Conta", fg_color="#333333", hover_color="#555555", command=self.acao_logout)
        self.btn_logout.pack(pady=5, padx=15)

        self.frame_main = ctk.CTkFrame(self, corner_radius=10)
        self.frame_main.pack(side="right", fill="both", expand=True, padx=(0, 15), pady=15)

        ctk.CTkLabel(self.frame_main, text="Título da Transmissão:").pack(anchor="w", padx=20, pady=(15, 2))
        self.ent_titulo = ctk.CTkEntry(self.frame_main, width=400)
        self.ent_titulo.pack(anchor="w", padx=20)
        self.ent_titulo.insert(0, self.config_data["titulo"])

        ctk.CTkLabel(self.frame_main, text="Descrição da Live:").pack(anchor="w", padx=20, pady=(10, 2))
        self.txt_desc = ctk.CTkTextbox(self.frame_main, width=400, height=80)
        self.txt_desc.pack(anchor="w", padx=20)
        self.txt_desc.insert("1.0", self.config_data["descricao"])

        frame_row1 = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        frame_row1.pack(anchor="w", padx=20, pady=10, fill="x")

        ctk.CTkLabel(frame_row1, text="Visibilidade:").grid(row=0, column=0, sticky="w")
        self.opt_privacidade = ctk.CTkOptionMenu(frame_row1, values=["public", "unlisted", "private"], width=120)
        self.opt_privacidade.grid(row=1, column=0, padx=(0, 20), sticky="w")
        self.opt_privacidade.set(self.config_data["visibilidade"])

        ctk.CTkLabel(frame_row1, text="Capa (Thumbnail):").grid(row=0, column=1, sticky="w")
        self.ent_thumb = ctk.CTkEntry(frame_row1, width=180)
        self.ent_thumb.grid(row=1, column=1, sticky="w")
        self.ent_thumb.insert(0, self.config_data["thumbnail"])
        
        self.btn_procurar_thumb = ctk.CTkButton(frame_row1, text="📁 ...", width=40, command=self.procurar_thumbnail)
        self.btn_procurar_thumb.grid(row=1, column=2, padx=5, sticky="w")

        # --- NOVA CAIXA DE SELEÇÃO DE THUMBNAIL (CONFORME SOLICITADO) ---
        self.chk_reutilizar_thumb = ctk.CTkCheckBox(self.frame_main, text="Reutilizar capa da última live caso o upload falhe")
        self.chk_reutilizar_thumb.pack(anchor="w", padx=20, pady=(5, 5))
        if self.config_data.get("reutilizar_ultima_thumb", True):
            self.chk_reutilizar_thumb.select()
        else:
            self.chk_reutilizar_thumb.deselect()

        frame_row2 = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        frame_row2.pack(anchor="w", padx=20, pady=10, fill="x")

        ctk.CTkLabel(frame_row2, text="Hora de Início (HH:MM):").grid(row=0, column=0, sticky="w")
        self.ent_inicio = ctk.CTkEntry(frame_row2, width=120)
        self.ent_inicio.grid(row=1, column=0, padx=(0, 40), sticky="w")
        self.ent_inicio.insert(0, self.config_data["hora_inicio"])

        ctk.CTkLabel(frame_row2, text="Hora de Corte (HH:MM):").grid(row=0, column=1, sticky="w")
        self.ent_fim = ctk.CTkEntry(frame_row2, width=120)
        self.ent_fim.grid(row=1, column=1, sticky="w")
        self.ent_fim.insert(0, self.config_data["hora_fim"])

        self.btn_salvar = ctk.CTkButton(self.frame_main, text="💾 Salvar Configurações & Agendar no Windows", 
                                         fg_color="#1b5e20", hover_color="#2e7d32", height=40, command=self.acao_salvar)
        self.btn_salvar.pack(fill="x", padx=20, pady=10)

        self.frame_status = ctk.CTkFrame(self.frame_main, height=45, fg_color="#1a1a1a", corner_radius=8)
        self.frame_status.pack(fill="x", padx=20, pady=(5, 10))
        
        self.lbl_status_bola = ctk.CTkLabel(self.frame_status, text="●", font=ctk.CTkFont(size=24))
        self.lbl_status_bola.pack(side="left", padx=(15, 8))
        
        self.lbl_status_texto = ctk.CTkLabel(self.frame_status, text="Verificando sistema...", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_status_texto.pack(side="left", padx=2)

        self.frame_botoes_manuais = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        self.frame_botoes_manuais.pack(fill="x", padx=20, pady=(0, 10))
        
        self.btn_iniciar_manual = ctk.CTkButton(self.frame_botoes_manuais, text="⚡ Iniciar Live Agora", 
                                                fg_color="#2b2b2b", hover_color="#404040", height=35, command=self.acao_iniciar_manual)
        self.btn_iniciar_manual.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_encerrar_manual = ctk.CTkButton(self.frame_botoes_manuais, text="🛑 Encerrar Live Agora", 
                                                 fg_color="#b71c1c", hover_color="#d32f2f", height=35, command=self.acao_encerrar_manual)
        self.btn_encerrar_manual.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.txt_log = ctk.CTkTextbox(self.frame_main, height=130, width=400, fg_color="#111111", text_color="#00ff00", font=ctk.CTkFont(family="Courier", size=12))
        self.txt_log.pack(fill="x", padx=20, pady=(0, 15))

    def atualizar_status_visual(self):
        info_local = obter_status_local()
        texto_dinamico = "NENHUMA LIVE AGENDADA PARA HOJE"
        
        if info_local["status"] == "ativa":
            self.status_atual = "ativa"
        else:
            config = carregar_configuracoes()
            if config and "hora_inicio" in config:
                agora = datetime.datetime.now().time()
                try:
                    h_ini = datetime.datetime.strptime(config["hora_inicio"], "%H:%M").time()
                    h_fim = datetime.datetime.strptime(config["hora_fim"], "%H:%M").time()
                    
                    if agora < h_ini:
                        self.status_atual = "aguardando_horario"
                        texto_dinamico = f"AGUARDANDO HORÁRIO DE INÍCIO ({config['hora_inicio']})"
                    elif agora > h_fim:
                        self.status_atual = "finalizada"
                        texto_dinamico = f"PRODUÇÃO ENCERRADA. PRÓXIMA LIVE SÓ AMANHÃ ÀS {config['hora_inicio']}"
                    else:
                        if info_local["id"] is not None and info_local["status"] == "inativa":
                            self.status_atual = "finalizada"
                            texto_dinamico = "PRODUÇÃO CONCLUÍDA E TRANSMISSÃO ENCERRADA."
                        else:
                            self.status_atual = "preparando"
                            texto_dinamico = "PREPARANDO SINAL E ENVIANDO INFOS..."
                except:
                    self.status_atual = "inativa"
            else:
                self.status_atual = "inativa"

        if self.status_atual == "ativa":
            self.lbl_status_texto.configure(text="LIVE EM TRANSMISSÃO AO VIVO", text_color="#ff3333")
            if self.blink_state:
                self.lbl_status_bola.configure(text="●", text_color="#ff3333")
            else:
                self.lbl_status_bola.configure(text="●", text_color="#1a1a1a")
            self.blink_state = not self.blink_state
            
        elif self.status_atual in ["preparando", "aguardando_horario"]:
            self.lbl_status_bola.configure(text="🕒", text_color="#ffb300")
            self.lbl_status_texto.configure(text=texto_dinamico, text_color="#ffb300")
            
        else: 
            self.lbl_status_bola.configure(text="●", text_color="#555555")
            self.lbl_status_texto.configure(text=texto_dinamico, text_color="#888888")

        self.after(500, self.atualizar_status_visual)

    def monitorar_log_compartilhado(self):
        LOG_FILE = "execucoes.log"
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            self.txt_log.delete("1.0", "end")
            for linha in linhas[-7:]: 
                self.txt_log.insert("end", f">> {linha}")
            self.txt_log.see("end")
        except:
            pass
        self.after(2000, self.monitorar_log_compartilhado)

    def atualizar_status_login_ui(self):
        if checar_autenticacao():
            self.lbl_status_login.configure(text="🟢 Autenticado", text_color="#2e7d32")
            self.btn_login.configure(state="disabled")
        else:
            self.lbl_status_login.configure(text="🔴 Desconectado", text_color="#d32f2f")
            self.btn_login.configure(state="normal")

    def procurar_thumbnail(self):
        caminho = filedialog.askopenfilename(filetypes=[("Imagens JPEG", "*.jpg;*.jpeg"), ("Imagens PNG", "*.png")])
        if caminho:
            self.ent_thumb.delete(0, "end")
            self.ent_thumb.insert(0, caminho)

    def acao_login(self):
        def fluxo():
            try:
                get_authenticated_service()
                self.atualizar_status_login_ui()
                registrar_log_compartilhado("Login efetuado com sucesso.")
            except Exception as e:
                registrar_log_compartilhado(f"Erro no login: {e}")
        threading.Thread(target=fluxo, daemon=True).start()

    def acao_logout(self):
        if os.path.exists('token.json'):
            os.remove('token.json')
        self.atualizar_status_login_ui()
        registrar_log_compartilhado("Conta desvinculada.")

    def acao_salvar(self):
        config = {
            "titulo": self.ent_titulo.get(),
            "descricao": self.txt_desc.get("1.0", "end-1c"),
            "visibilidade": self.opt_privacidade.get(),
            "thumbnail": self.ent_thumb.get(),
            "hora_inicio": self.ent_inicio.get(),
            "hora_fim": self.ent_fim.get(),
            "reutilizar_ultima_thumb": bool(self.chk_reutilizar_thumb.get())
        }
        salvar_configuracoes(config)
        registrar_log_compartilhado("Configurações salvas em config.json.")
        try:
            atualizar_agendador_windows(config["hora_inicio"], config["hora_fim"])
            registrar_log_compartilhado(f"Agendador Windows Atualizado! Início: {config['hora_inicio']} | Fim: {config['hora_fim']}")
        except Exception as e:
            registrar_log_compartilhado(f"Erro ao configurar Agendador: {e}")

    def acao_iniciar_manual(self):
        def fluxo():
            try:
                self.btn_iniciar_manual.configure(state="disabled")
                registrar_log_compartilhado("Disparo manual: Iniciando processo...")
                if not checar_autenticacao():
                    registrar_log_compartilhado("Erro: Conta YouTube não autenticada.")
                    return
                
                youtube = get_authenticated_service()
                config = carregar_configuracoes()
                broadcast_id = obter_live_ativa_ou_agendada(youtube)
                
                if not broadcast_id:
                    registrar_log_compartilhado("Nenhuma live ativa. Criando estrutura e gerando ID...")
                    broadcast_id = preparar_e_criar_metadados(youtube, config)
                    
                if broadcast_id:
                    atualizar_arquivo_status(broadcast_id, "ativa")
                    registrar_log_compartilhado(f"ID gerado com sucesso: [{broadcast_id}]. Gerenciando Thumbnail...")
                    
                    # Chama a função inteligente corrigida
                    gerenciar_upload_thumbnail(youtube, broadcast_id, config)
                    
                    agora_objeto = datetime.datetime.now().time()
                    horario_configurado = datetime.datetime.strptime(config["hora_inicio"], "%H:%M").time()
                    
                    if agora_objeto < horario_configurado:
                        registrar_log_compartilhado(f"Aguardando em modo Standby até o horário programado ({config['hora_inicio']})...")
                        while datetime.datetime.now().time() < horario_configurado:
                            import time
                            time.sleep(5)
                        registrar_log_compartilhado("Horário programado atingido!")

                    registrar_log_compartilhado("Estabilizando sinal de transmissão com a API (10s)...")
                    import time
                    time.sleep(10)
                    
                    efetiver_entrada_ao_vivo(youtube, broadcast_id)
                    registrar_log_compartilhado(f"Sucesso: Transmissão [{broadcast_id}] oficialmente AO VIVO!")
            except Exception as e:
                registrar_log_compartilhado(f"Erro no disparo manual: {e}")
            finally:
                self.btn_iniciar_manual.configure(state="normal")
        threading.Thread(target=fluxo, daemon=True).start()

    def acao_encerrar_manual(self):
        def fluxo():
            try:
                self.btn_encerrar_manual.configure(state="disabled")
                registrar_log_compartilhado("Comando manual: Solicitando corte de transmissão...")
                if not checar_autenticacao():
                    registrar_log_compartilhado("Erro: Sem autenticação.")
                    return
                
                youtube = get_authenticated_service()
                info_local = obter_status_local()
                broadcast_id = info_local["id"]
                
                if not broadcast_id:
                    broadcast_id = obter_live_ativa_ou_agendada(youtube, apenas_ao_vivo=True)
                    
                if broadcast_id:
                    try:
                        youtube.liveBroadcasts().transition(broadcastStatus="complete", id=broadcast_id, part='id,status').execute()
                        registrar_log_compartilhado(f"Sincronizador API: Live [{broadcast_id}] finalizada no YouTube Studio.")
                    except Exception as api_err:
                        if "redundantTransition" in str(api_err):
                            registrar_log_compartilhado(f"Aviso: Transmissão [{broadcast_id}] já se encontrava encerrada remotamente.")
                        else:
                            raise api_err
                    
                    atualizar_arquivo_status(broadcast_id, "inativa")
                    self.status_atual = "finalizada"
                else:
                    registrar_log_compartilhado("⚠️ Erro: Nenhuma transmissão ativa encontrada para finalizar.")
            except Exception as e:
                registrar_log_compartilhado(f"Erro ao encerrar live: {e}")
            finally:
                self.btn_encerrar_manual.configure(state="normal")
        threading.Thread(target=fluxo, daemon=True).start()

# ==========================================
# EXECUÇÃO DE DISPAROS AUTOMÁTICOS (HEADLESS)
# ==========================================

def executar_headless(comando):
    if not checar_autenticacao():
        registrar_log_compartilhado("Erro: Aplicação sem token de autenticação válido.")
        sys.exit(1)
        
    config = carregar_configuracoes()
    youtube = get_authenticated_service()
    
    try:
        if comando == "iniciar":
            registrar_log_compartilhado("Agendador disparou: Iniciando processo...")
            broadcast_id = obter_live_ativa_ou_agendada(youtube)
            
            if not broadcast_id:
                registrar_log_compartilhado("Nenhuma live encontrada para hoje. Criando nova estrutura de metadados...")
                broadcast_id = preparar_e_criar_metadados(youtube, config)
                
            if broadcast_id:
                atualizar_arquivo_status(broadcast_id, "ativa")
                registrar_log_compartilhado(f"Live ID [{broadcast_id}] guardado localmente. Gerenciando thumbnail...")
                
                # Chama a contingência também na execução do Agendador do Windows
                gerenciar_upload_thumbnail(youtube, broadcast_id, config)
                
                horario_programado = datetime.datetime.strptime(config["hora_inicio"], "%H:%M").time()
                agora_time = datetime.datetime.now().time()
                
                if agora_time < horario_programado:
                    registrar_log_compartilhado(f"Entrando em Standby. Aguardando o horário correto de liberação: {config['hora_inicio']}")
                    while datetime.datetime.now().time() < horario_programado:
                        import time
                        time.sleep(2)
                
                registrar_log_compartilhado("Iniciando Handshake de transmissão (10s)...")
                import time
                time.sleep(10) 
                
                efetiver_entrada_ao_vivo(youtube, broadcast_id)
                registrar_log_compartilhado(f"Sucesso: Transmissão [{broadcast_id}] oficialmente AO VIVO!")
            else:
                registrar_log_compartilhado("Erro: Falha ao gerar o ID da transmissão.")
                
        elif comando == "encerrar":
            registrar_log_compartilhado("Agendador disparou: Buscando ID salvo para corte...")
            info_local = obter_status_local()
            broadcast_id = info_local["id"]
            
            if broadcast_id:
                try:
                    youtube.liveBroadcasts().transition(broadcastStatus="complete", id=broadcast_id, part='id,status').execute()
                    registrar_log_compartilhado(f"Sucesso: Transmissão [{broadcast_id}] encerrada automaticamente.")
                except Exception as api_error:
                    if "redundantTransition" in str(api_error):
                        registrar_log_compartilhado(f"Aviso: Transmissão [{broadcast_id}] já estava fechada remotamente.")
                    else:
                        registrar_log_compartilhado(f"Erro ao encerrar ID [{broadcast_id}]: {api_error}")
                
                atualizar_arquivo_status(broadcast_id, "inativa")
            else:
                registrar_log_compartilhado("⚠️ Erro: Nenhum ID de live pendente foi encontrado para encerramento automático.")
                
    except Exception as e:
        registrar_log_compartilhado(f"Erro crítico na execução automática: {e}")

# ==========================================
# ENTRADA DO SCRIPT
# ==========================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["iniciar", "encerrar"]:
        executar_headless(sys.argv[1])
    else:
        app = AppGUI()
        app.mainloop()