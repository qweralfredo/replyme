import smtplib
import time
from email.message import EmailMessage

# Lista de cenários com variados sentimentos, urgências e tópicos
scenarios = [
    {
        "subject": "Reclamação: Produto não liga - Urgente!",
        "from": "cliente_bravo@gmail.com",
        "body": "Meu produto veio com defeito, quero meu dinheiro de volta urgente! Comprei o modelo X1 ontem e já não liga."
    },
    {
        "subject": "Elogio ao atendimento excelente",
        "from": "cliente_feliz@hotmail.com",
        "body": "Gostaria de parabenizar a equipe de suporte. O atendente João foi muito educado e resolveu meu problema em 5 minutos. Muito obrigado!"
    },
    {
        "subject": "Dúvida sobre a fatura de Novembro",
        "from": "carlos.silva@empresa.com",
        "body": "Olá, analisei a fatura enviada hoje e notei uma cobrança duplicada no serviço de cloud. Poderiam revisar e emitir uma nova via, por favor?"
    },
    {
        "subject": "Cancelamento de assinatura",
        "from": "marcos_descontente@yahoo.com",
        "body": "Não tenho mais interesse em usar a plataforma de vocês. Está muito cara e não entrega o que promete. Quero cancelar imediatamente antes da próxima cobrança."
    },
    {
        "subject": "Proposta de Parceria Comercial",
        "from": "diretoria@agenciadigital.com",
        "body": "Prezados, somos uma agência de marketing e temos interesse em integrar o nosso software com a solução de vocês. Gostaria de marcar uma reunião para conversar sobre uma parceria."
    },
    {
        "subject": "Sugestão de nova funcionalidade",
        "from": "usuario.ativo@techmail.com",
        "body": "Oi pessoal, adoro o app de vocês! Seria incrível se na próxima atualização vocês colocassem um botão de 'modo escuro'. Acho que todo mundo iria gostar."
    },
    {
        "subject": "URGENTE: Conta hackeada",
        "from": "alerta_seguranca@gmail.com",
        "body": "Por favor me ajudem! Alguém invadiu minha conta e mudou meu e-mail e telefone de recuperação. Não consigo mais acessar e tenho dados sensíveis lá. Socorro!"
    },
    {
        "subject": "Atualização de endereço de entrega",
        "from": "joana_compras@gmail.com",
        "body": "Fiz um pedido ontem (ID: 99812) e percebi que coloquei o número da casa errado. O correto é 125 e não 152. Conseguem alterar antes do envio?"
    },
    {
        "subject": "Vaga de Desenvolvedor Sênior",
        "from": "dev_candidato@dev.com",
        "body": "Boa tarde, vi a vaga anunciada no LinkedIn e estou enviando meu currículo em anexo para consideração. Tenho 10 anos de experiência com Python."
    },
    {
        "subject": "Dificuldade de acesso ao sistema antigo",
        "from": "suporte_ti@cliente.com.br",
        "body": "Nossa equipe não consegue mais fazer login na versão legado do sistema desde a atualização de ontem. Pode nos dar uma previsão de retorno?"
    }
]

print(f"Iniciando envio de {len(scenarios)} cenários de teste para localhost:1025 (Mailpit)...\n")

try:
    with smtplib.SMTP('localhost', 1025) as s:
        for i, scenario in enumerate(scenarios, 1):
            msg = EmailMessage()
            msg.set_content(scenario["body"])
            msg['Subject'] = scenario["subject"]
            msg['From'] = scenario["from"]
            msg['To'] = 'suporte@replyme.local'
            
            s.send_message(msg)
            print(f"[{i}/{len(scenarios)}] Enviado: {scenario['subject']}")
            
            # Pequena pausa para garantir a ordem de chegada
            time.sleep(0.5)
            
    print("\nTodos os e-mails foram enviados com sucesso!")
except ConnectionRefusedError:
    print("Erro: Não foi possível conectar. O container do mailpit está rodando com a porta 1025 exposta?")
