# Análise do Projeto: Planilha de Gerenciamento Forex

Após revisar o código-fonte do repositório, identifiquei que este é um **ecossistema completo para gestão profissional de trading (Forex/B3)**. O sistema permite aos traders registrar, analisar e sincronizar suas operações financeiras de forma automatizada e manual.

A arquitetura do projeto é dividida em três pilares principais: **Frontend (Dashboard/Planilha)**, **Integração com MetaTrader 5 (MT5)**, e **Backend/Infraestrutura**.

---

## 1. O Frontend: `Planilha_Gustavo_Pedrosa_FX.html`

Este é o arquivo central do projeto (~180KB, 3700+ linhas) e funciona como uma **Single Page Application (SPA)** construída inteiramente com HTML, CSS puro (sem uso de frameworks como Tailwind) e JavaScript Vanilla. 

### Principais Características do Dashboard:
- **Gestão de Múltiplas Contas:** Permite gerenciar mais de uma conta de trading simultaneamente através de abas.
- **Armazenamento Local e Persistência:** Utiliza o `localStorage` (chave `gustavoPedrosaFX_v1`) para salvar os dados offline, com suporte a migração de versões anteriores (`forexTrackerPro_v2`).
- **Navegação e Funcionalidades (Menu Lateral):**
  - **Diário:** Registro detalhado dos trades, resultados (WIN/LOSS) e emoções sentidas (Ansioso, Confiante, etc.).
  - **Calendário & Evolução:** Visualização de P&L (Profit and Loss) em calendários anuais/mensais e gráficos de evolução.
  - **Análises & Heatmap:** Ferramentas visuais avançadas para analisar performance por par de moedas e semanas.
  - **Exportação/Importação:** Capacidade de exportar dados para CSV ou **importar relatórios HTML nativos do MT5** diretamente pelo navegador.
- **Sistema de Login Integrado:** Contém uma interface de overlay de login (`#loginOverlay`), indicando integração com um sistema de autenticação remoto (provavelmente Supabase).

---

## 2. A Automação MT5: `GPFX_Sync.mq5`

Para não depender apenas de inserção manual, o projeto inclui um **Expert Advisor (Robô) para MetaTrader 5** escrito em linguagem MQL5.

- **Objetivo:** Ler o histórico de transações fechadas na plataforma MT5 do usuário e enviar os dados automaticamente para a nuvem.
- **Como funciona:** Ele escaneia as "Deals" (operações) de compra/venda e envia um payload JSON para uma **Edge Function** chamada `ingest-trades`.
- **Segurança:** Utiliza uma chave de API (`InpApiKey`) gerada no painel do usuário e validada pelo servidor. Não envia nem armazena senhas da corretora.

---

## 3. Backend e Infraestrutura

Apesar do projeto ser focado no frontend, ele utiliza ferramentas modernas de backend e deployment:

### Supabase (Banco de Dados e Autenticação)
- O arquivo `0003_create_mt5_connections_table.sql` revela o uso do **Supabase** (PostgreSQL).
- Foi criada a tabela `mt5_connections` que armazena hashes (SHA-256) das chaves do robô MT5 geradas para os usuários.
- **Segurança Robusta (RLS):** As *Row Level Security policies* garantem que os usuários só possam ver e gerenciar as chaves das próprias contas. A Edge Function autentica o robô cruzando a chave enviada com este hash no banco.

### Docker & Traefik (`docker-compose.yml` e `Dockerfile`)
- O frontend é conteinerizado usando uma imagem leve do **Nginx** (`nginx:alpine`).
- O `docker-compose.yml` utiliza **Traefik** como proxy reverso, configurando automaticamente rotas e certificados SSL (Let's Encrypt). O dashboard é servido em um domínio específico (ex: `planilha..testedev.online`).

---

## Conclusão

Você construiu uma plataforma altamente otimizada, que não depende de grandes bibliotecas Javascript no frontend, resultando em extrema velocidade e eficiência. O ecossistema é muito bem pensado, permitindo uso completamente offline/local (via `localStorage`) ao mesmo tempo em que oferece funcionalidades avançadas na nuvem, como a sincronização automática via robô MT5 e o backup via Supabase.
