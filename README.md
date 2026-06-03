# ReplyMe Cognitive Hub

O ReplyMe é um sistema de inteligência artificial desenhado para atuar como um funil inteligente para caixas de e-mail (Customer Service, Suporte, Vendas). Ele captura mensagens brutas, envia para o Google Gemini para extrair contexto (urgência, sentimento, categoria e resumo) e gera um rascunho de resposta, apresentando tudo em um Dashboard Kanban ágil e totalmente autônomo.

## ✨ Novidades e Enriquecimentos Recentes

O sistema foi substancialmente evoluído para suportar fluxos agênticos e integrações de alto nível:
- **Suporte a Servidores MCP (Model Context Protocol):** Agora o ReplyMe atua como um MCP Client nativo. Ele pode se conectar a scripts locais (ex: Python) ou remotos, carregar as "Tools" disponíveis e permitir que o Gemini interaja autonomamente com outros sistemas.
- **Integração com Frappe Helpdesk:** Um servidor Frappe completo (com MariaDB e Redis) roda de forma isolada, e um script MCP (`frappe_helpdesk_mcp.py`) permite que a IA converta e-mails diretamente em tickets no Helpdesk de forma automatizada.
- **Colunas Agênticas no Kanban:** O usuário pode vincular um ou mais Servidores MCP a uma coluna específica. Sempre que o classificador de IA mover um e-mail para aquela coluna (com base nas regras da empresa), o ReplyMe disparará o Servidor MCP vinculado, executando tarefas automáticas (como abrir o ticket).
- **Interface de Teste Integrada:** Um modal "Testar MCP Server" permite testar as ferramentas instaladas de maneira isolada com o LLM diretamente pelo navegador.
- **UI/UX Premium:** Design renovado com Glassmorphism refinado, barras de rolagem personalizadas (`::-webkit-scrollbar`) e modais animados para proporcionar a melhor experiência do usuário.
- **Gemini Context Caching:** Utiliza a API avançada do Google para fazer o upload em cache de arquivos e regras no momento em que o servidor sobe, acelerando respostas e reduzindo o consumo de tokens.

## 🏗️ Arquitetura

O projeto roda inteiramente via Docker e é composto por containers independentes, porém integrados:
- **DB (PostgreSQL):** Banco de dados relacional armazenando as mensagens, metadados de IA e regras do Kanban.
- **App (Python Worker):** O cérebro do sistema. Fica em loop escutando novos e-mails (via Mailpit), usando `instructor` para forçar respostas estruturadas (JSON), e orquestra a comunicação MCP via `mcp.client`.
- **PHP API:** Backend ultra-rápido (na porta 8080) que faz a ponte entre o frontend, o banco de dados e as requisições síncronas do MCP Test.
- **Frappe Helpdesk Stack:** Ambiente nativo do Frappe ERP (App, Redis, MariaDB) rodando na porta `8001` para gerenciamento oficial de chamados de suporte.
- **Frontend (Vanilla JS/CSS):** Um Kanban intuitivo (Glassmorphism + Dark Mode) com arrastar-e-soltar e modais dinâmicos.
- **Mailpit:** Servidor de e-mail local (in-memory) usado para receber testes práticos simulando uma caixa de e-mail real.

## 🚀 Como Iniciar (How-To)

### 1. Pré-requisitos
- **Docker e Docker Compose** instalados na sua máquina.
- **Python 3.10+** (apenas se quiser rodar scripts auxiliares fora do docker).
- **Chave de API do Google Gemini**. ([Pegue a sua aqui](https://aistudio.google.com/app/apikey))

### 2. Configurando o Ambiente
Crie as variáveis de ambiente necessárias. O container Python precisa da chave do Gemini.  
No arquivo `docker-compose.yml`, você pode inserir a chave direto na sessão do serviço `app`, ou criar um `.env` na raiz do projeto (recomendado) e referenciar a chave:
```env
GOOGLE_API_KEY=sua_chave_aqui
```

### 3. Rodando o Projeto
Com o Docker aberto, abra o terminal na raiz do projeto e rode:

```bash
docker-compose up -d --build
```
Isso fará o download das imagens, criará o banco de dados com as tabelas corretas, e inicializará o Frappe Helpdesk (pode demorar alguns minutos na primeira execução para baixar as dependências NodeJS e Python do Frappe).

## 🧪 Como Testar e Usar

### Envio de E-mails Simulados
Como o projeto é agnóstico, nós usamos o **Mailpit** para interceptar os e-mails de teste. O Worker em Python fará a leitura periódica.
Para enviar 10 e-mails de cenário de suporte e vendas, execute:
```bash
python send_test.py
```

### Configurando a Automação MCP
1. Acesse o **Painel Kanban**.
2. Clique no ícone da engrenagem no cabeçalho (Configurações) e vá em **Servidores MCP**.
3. Adicione um servidor MCP (ex: `python /app/src/mcp/frappe_helpdesk_mcp.py`). Você pode usar o botão 🧪 para testá-lo manualmente.
4. Clique na engrenagem de uma Coluna (ex: "Suporte"), selecione o MCP recém-criado e digite o Prompt (ex: *"Abra um chamado com os dados deste e-mail"*).
5. Envie um e-mail de teste. Ao cair na coluna Suporte, o robô automaticamente abrirá o ticket no sistema externo!

## 🌐 Acessos e Portas do Sistema

- **Painel Kanban (Frontend):** [http://localhost:8080/public/](http://localhost:8080/public/)
- **Frappe Helpdesk:** [http://helpdesk.localhost:8001](http://helpdesk.localhost:8001) (Usuário: `Administrator` / Senha: `admin`)
- **Mailpit (Ver E-mails Brutos):** [http://localhost:8025/](http://localhost:8025/)
- **Servidor SMTP (Para Enviar):** `localhost:1025`
- **Banco de Dados PostgreSQL:** `localhost:5433` (Usuário: `postgres`, Senha: `password`, DB: `replayme_db`)

## 💡 Evolução Tecnológica
A infraestrutura agora está pronta para atuar como um Multi-Agent System (MAS), não mais restrito a apenas triar e-mails, mas capaz de atuar em inúmeras superfícies de sistema graças ao ecossistema MCP.
