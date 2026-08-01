# Guia de Instalação no Portainer (VPS)

O seu projeto já está muito bem preparado para rodar em produção, pois inclui um `Dockerfile` e um `docker-compose.yml` configurado para usar o Traefik como proxy reverso. 

Como o seu arquivo `docker-compose.yml` faz referência a um arquivo local (`file: ./Planilha_Gustavo_Pedrosa_FX.html`), a forma mais fácil e recomendada de fazer o deploy no Portainer é **conectando-o diretamente ao seu repositório Git**.

Aqui está o passo a passo completo:

## Pré-requisitos na VPS
1. Ter o **Docker** e o **Portainer** instalados.
2. Ter uma rede chamada `traefik_public` criada no Docker (onde o seu proxy Traefik roda).
3. O seu projeto precisa estar com as alterações enviadas (commit/push) para o seu repositório (ex: GitHub, GitLab ou Bitbucket).

---

## Passo 1: Ajustar o domínio (Opcional, mas recomendado)
Antes de fazer o push para o Git, notei que no arquivo `docker-compose.yml`, a regra do domínio tem dois pontos (..):
```yaml
- traefik.http.routers.planilha-forex.rule=Host(`planilha..testedev.online`)
```
Recomendo corrigir isso para o seu domínio real, por exemplo:
`- traefik.http.routers.planilha-forex.rule=Host('planilha.testedev.online')`

---

## Passo 2: Criar a Stack no Portainer

1. Acesse o painel web do seu **Portainer**.
2. Clique no seu ambiente (geralmente **"Local"** ou o nome do seu Swarm).
3. No menu lateral esquerdo, clique em **Stacks**.
4. Clique no botão azul **"+ Add stack"** no canto superior direito.

## Passo 3: Configurar o Repositório Git

Na tela de criação da Stack:
1. Dê um nome para a stack (ex: `planilha-forex`).
2. Em **Build method** (Método de construção), selecione a opção **"Repository"**.
3. Em **Repository URL**, cole o link do seu repositório Git (ex: `https://github.com/LuizPedrosa77/Planilha-forex.git`).
4. Se o repositório for privado, ative a opção **"Authentication"** e insira seu usuário e Personal Access Token (PAT) do GitHub.
5. Em **Compose path**, deixe como `docker-compose.yml` (já que esse é o nome do seu arquivo na raiz).

## Passo 4: Deploy Automático (Recomendado)

> [!TIP]
> **Dica de Ouro:** O Portainer permite ativar o "Automatic updates" (Atualizações automáticas). 
> Se você ativar a opção **"GitOps updates"** no Portainer, sempre que você modificar a planilha e fizer um `git push` no seu computador, o Portainer vai puxar a atualização sozinho e reiniciar a planilha em 1 ou 2 minutos!

1. Na seção **Automatic updates**, ative a chave (Polling ou Webhook, o Polling é mais fácil, basta definir para checar a cada 5 minutos).
2. Role até o final da página e clique no botão **"Deploy the stack"**.

## Passo 5: Pronto!
O Portainer vai baixar o seu código do GitHub, ler a configuração (`Configs`), mapear o HTML para o Nginx (`nginx:alpine`) e colocar no ar através do Traefik.

Acesse o domínio que você configurou (ex: `https://planilha.testedev.online`) e sua planilha já estará lá, rodando 24 horas por dia!
