import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg.set_content("Meu produto veio com defeito, quero meu dinheiro de volta urgente! Comprei o modelo X1 ontem e já não liga.")
msg['Subject'] = 'Reclamação de Produto'
msg['From'] = 'cliente_bravo@gmail.com'
msg['To'] = 'suporte@replyme.local'

print("Enviando e-mail de teste para localhost:1025 (Mailpit)...")
try:
    with smtplib.SMTP('localhost', 1025) as s:
        s.send_message(msg)
    print("E-mail enviado com sucesso!")
except ConnectionRefusedError:
    print("Erro: Não foi possível conectar. O container do mailpit está rodando com a porta 1025 exposta?")
