# ReplyMe Cognitive Hub

O ReplyMe é um sistema de inteligência artificial desenhado para atuar como um funil inteligente para caixas de e-mail (Customer Service, Suporte, Vendas). Ele captura mensagens brutas, envia para o Google Gemini para extrair contexto (urgência, sentimento, categoria e resumo) e gera um rascunho de resposta, apresentando tudo em um Dashboard Kanban ágil.

## 🏗️ Arquitetura

O projeto roda inteiramente via Docker e é composto por 4 containers principais:
- **DB (PostgreSQL):** Banco de dados relacional armazenando as mensagens e metadados de IA.
- **App (Python Worker):** O cérebro do sistema. Fica em loop escutando novos e-mails (via Mailpit) e chamando a API do Gemini via `instructor` para forçar respostas estruturadas (JSON).
- **PHP API:** Backend ultra-rápido que expõe os dados do PostgreSQL para o frontend usando PDO.
- **Frontend (Vanilla JS/CSS):** Um Kanban intuitivo (Glassmorphism + Dark Mode) com arrastar-e-soltar para mover e-mails entre as colunas "Inbox", "Processando", "Revisão" e "Concluído".
- **Mailpit:** Servidor de e-mail local (in-memory) usado para receber testes práticos simulando uma caixa de e-mail real.

## 🚀 Como Iniciar (How-To)

### 1. Pré-requisitos
- **Docker e Docker Compose** instalados na sua máquina.
- **Python 3.10+** (apenas se quiser rodar os scripts de teste localmente fora do docker).
- **Chave de API do Google Gemini**. ([Pegue a sua aqui](https://aistudio.google.com/app/apikey))

### 2. Configurando o Ambiente
Crie as variáveis de ambiente necessárias. O container Python precisa da chave do Gemini.  
No arquivo `docker-compose.yml`, você pode inserir a chave direto na sessão do serviço `app`, ou criar um `.env` na raiz do projeto (recomendado) e referenciar.

*(Nota: O worker está programado para não dar crash sem a chave, mas ele falhará na hora de classificar a mensagem se não houver a `GOOGLE_API_KEY` injetada no ambiente).*

### 3. Rodando o Projeto
Com o Docker aberto, abra o terminal na raiz do projeto e rode:

```bash
docker compose up -d --build
```
Isso fará o download das imagens, criará o banco de dados com as tabelas corretas e subirá toda a infraestrutura.

## 🧪 Como Testar (Simulando a Entrada de E-mails)

Como o projeto é agnóstico, nós usamos o **Mailpit** para interceptar os e-mails de teste. O Worker em Python fará o *polling* automático (leitura a cada 5 segundos) dessa caixa falsa.

### Opção 1: Usando o Script de Teste (Recomendado)
Execute o script em Python na raiz do projeto para disparar um e-mail de reclamação padrão:
```bash
python send_test.py
```

### Opção 2: Pelo Terminal / cURL / Swaks
Você pode apontar qualquer software de disparo para o localhost na porta SMTP e enviar uma mensagem falsa:
```bash
swaks --to suporte@replyme.local --from cliente@gmail.com --server localhost --port 1025 --body "Preciso de ajuda urgente"
```

## 🌐 Acessos e Portas do Sistema

- **Painel Kanban (Frontend):** [http://localhost:8080/public/](http://localhost:8080/public/)
- **Mailpit (Ver E-mails Brutos):** [http://localhost:8025/](http://localhost:8025/)
- **Servidor SMTP (Para Enviar):** `localhost:1025`
- **Banco de Dados PostgreSQL:** `localhost:5433` (Usuário: `postgres`, Senha: `password`, DB: `replayme_db`)

## 💡 Próximos Passos (Evolução)
Se desejar levar o projeto para produção, substitua a leitura do Mailpit no arquivo `src/main.py` por uma conexão IMAP real (ex: Gmail) ou por um recebimento de Webhook via SendGrid na API PHP.
