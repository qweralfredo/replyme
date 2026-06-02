import time
import random
import structlog
from sqlmodel import Session
from src.database import engine
from src.models import Email

logger = structlog.get_logger(__name__)

MOCK_SENDERS = ["cliente_feliz@email.com", "cliente_bravo@email.com", "duvida_rapida@email.com", "parceria@empresa.com", "reclamacao@consumidor.com"]
MOCK_SUBJECTS = ["Sobre meu pedido", "Problema com a entrega", "Dúvida sobre o plano", "Gostei muito do serviço", "Proposta comercial", "Meu produto veio com defeito"]
MOCK_BODIES = [
    "Olá, gostaria de saber onde está o meu pedido número #12345. Já passou do prazo.",
    "Estou muito decepcionado com o produto, ele quebrou no primeiro dia. Quero meu dinheiro de volta.",
    "Oi equipe! Só passando pra dizer que o suporte foi excelente. Parabéns!",
    "Vocês têm algum plano empresarial para mais de 50 pessoas?",
    "A entrega atrasou e ninguém me avisa de nada. Absurdo!",
    "Tenho interesse em uma parceria comercial. Qual é o telefone de contato?",
]

def run_simulator():
    logger.info("Starting email simulator...")
    while True:
        try:
            with Session(engine) as session:
                new_email = Email(
                    sender=random.choice(MOCK_SENDERS),
                    subject=random.choice(MOCK_SUBJECTS),
                    body=random.choice(MOCK_BODIES),
                    status="inbox"
                )
                session.add(new_email)
                session.commit()
                logger.info("Simulated new incoming email", subject=new_email.subject)
        except Exception as e:
            logger.error("Simulator error", error=str(e))
        
        # Wait 10 to 20 seconds before inserting another
        time.sleep(random.randint(10, 20))

if __name__ == "__main__":
    run_simulator()
