import streamlit as st
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import io
import base64

# Configuração da página
st.set_page_config(
    page_title="Envio de Documentos - Condomínio",
    page_icon="📄",
    layout="centered"
)

# CSS customizado para deixar mais bonito
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Função para enviar email
def enviar_email(dados_prestador, arquivos):
    try:
        # Configurações do email (use variáveis de ambiente no deploy)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        email_remetente = st.secrets["EMAIL_REMETENTE"]  # Configure no Streamlit Secrets
        senha_email = st.secrets["SENHA_EMAIL"]  # Configure no Streamlit Secrets
        email_destinatario = st.secrets["EMAIL_CONDOMINIO"]  # Email do condomínio
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = email_destinatario
        msg['Subject'] = f"Documentos - {dados_prestador['nome']} ({dados_prestador['servico']})"
        
        # Corpo do email
        corpo_email = f"""
        Novos documentos recebidos via sistema:
        
        📋 DADOS DO PRESTADOR:
        • Nome: {dados_prestador['nome']}
        • Serviço: {dados_prestador['servico']}
        • WhatsApp: {dados_prestador['telefone']}
        • Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        
        📎 ARQUIVOS ANEXADOS: {len(arquivos)} arquivo(s)
        
        ---
        Sistema de Envio de Documentos - Condomínio
        """
        
        msg.attach(MIMEText(corpo_email, 'plain'))
        
        # Anexar arquivos
        for arquivo in arquivos:
            if arquivo is not None:
                # Ler arquivo
                arquivo_bytes = arquivo.read()
                arquivo.seek(0)  # Reset file pointer
                
                # Criar anexo
                anexo = MIMEBase('application', 'octet-stream')
                anexo.set_payload(arquivo_bytes)
                encoders.encode_base64(anexo)
                anexo.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {arquivo.name}'
                )
                msg.attach(anexo)
        
        # Conectar e enviar
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_remetente, senha_email)
        text = msg.as_string()
        server.sendmail(email_remetente, email_destinatario, text)
        server.quit()
        
        return True, "Email enviado com sucesso!"
        
    except Exception as e:
        return False, f"Erro ao enviar email: {str(e)}"

# Função para formatar telefone
def formatar_telefone(telefone):
    if not telefone:
        return ""
    numeros = ''.join(filter(str.isdigit, telefone))
    if len(numeros) == 11:
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    elif len(numeros) == 10:
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
    return telefone

# Interface principal
def main():
    # Header
    st.markdown("# 📄 Envio de Documentos")
    st.markdown("### Envie sua nota fiscal e boleto de forma rápida e fácil")
    st.markdown("---")
    
    # Verificar se já enviou (usando session_state)
    if 'enviado' not in st.session_state:
        st.session_state.enviado = False
    
    if st.session_state.enviado:
        st.markdown('<div class="success-box">✅ <strong>Documentos enviados com sucesso!</strong><br>Obrigado pelo envio. Os documentos foram recebidos pelo condomínio.</div>', unsafe_allow_html=True)
        
        if st.button("📤 Enviar Novos Documentos"):
            st.session_state.enviado = False
            st.rerun()
        return
    
    # Formulário
    with st.form("form_documentos", clear_on_submit=True):
        # Dados do prestador
        st.subheader("👤 Dados do Prestador")
        
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo *", placeholder="Ex: João da Silva")
        
        with col2:
            servico = st.selectbox("Tipo de Serviço *", [
                "",
                "Pedreiro",
                "Eletricista", 
                "Encanador",
                "Pintor",
                "Jardinagem",
                "Limpeza",
                "Segurança",
                "Manutenção Geral",
                "Outro"
            ])
        
        telefone = st.text_input("WhatsApp (opcional)", placeholder="(11) 99999-9999")
        
        st.markdown("---")
        
        # Upload de arquivos
        st.subheader("📎 Documentos")
        st.markdown('<div class="info-box">📋 <strong>Tipos aceitos:</strong> PDF, JPG, PNG<br>📏 <strong>Tamanho máximo:</strong> 10MB por arquivo</div>', unsafe_allow_html=True)
        
        arquivos = st.file_uploader(
            "Selecione os arquivos (Nota Fiscal, Boleto, Recibo)",
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png']
        )
        
        # Preview dos arquivos
        if arquivos:
            st.write("**Arquivos selecionados:**")
            for i, arquivo in enumerate(arquivos):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if arquivo.type.startswith('image'):
                        st.write("🖼️")
                    else:
                        st.write("📄")
                with col2:
                    st.write(f"{arquivo.name}")
                with col3:
                    size_mb = arquivo.size / (1024 * 1024)
                    st.write(f"{size_mb:.1f}MB")
        
        # Botão de envio
        st.markdown("---")
        enviado = st.form_submit_button("📤 Enviar Documentos")
        
        if enviado:
            # Validações
            erros = []
            if not nome.strip():
                erros.append("Nome é obrigatório")
            if not servico:
                erros.append("Tipo de serviço é obrigatório")
            if not arquivos:
                erros.append("Pelo menos um arquivo é obrigatório")
            
            # Validar tamanho dos arquivos
            for arquivo in arquivos:
                if arquivo.size > 10 * 1024 * 1024:  # 10MB
                    erros.append(f"Arquivo '{arquivo.name}' excede 10MB")
            
            if erros:
                for erro in erros:
                    st.error(f"❌ {erro}")
            else:
                # Dados do prestador
                dados_prestador = {
                    'nome': nome.strip(),
                    'servico': servico,
                    'telefone': formatar_telefone(telefone)
                }
                
                # Enviar email
                with st.spinner('📤 Enviando documentos...'):
                    sucesso, mensagem = enviar_email(dados_prestador, arquivos)
                
                if sucesso:
                    st.session_state.enviado = True
                    st.rerun()
                else:
                    st.error(f"❌ {mensagem}")

# Sidebar com informações
with st.sidebar:
    st.markdown("### ℹ️ Informações")
    st.markdown("""
    **Como usar:**
    1. Preencha seus dados
    2. Selecione os arquivos
    3. Clique em "Enviar"
    
    **Tipos de arquivo aceitos:**
    - PDF (nota fiscal, boleto)
    - JPG/PNG (fotos de documentos)
    
    **Tamanho máximo:** 10MB por arquivo
    
    ---
    **Dúvidas?**
    Entre em contato pelo WhatsApp informado no formulário.
    """)

if __name__ == "__main__":
    main()