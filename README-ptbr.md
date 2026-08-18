# Google My Business Manager

Plataforma para acompanhar resultados do Google Business Profile (GBP), responder avaliações, publicar posts e gerar relatórios de forma simples.

Foi pensada para:
- Agências de marketing local
- Donos de negócio
- Times de atendimento/comercial

Você não precisa saber programar para usar no dia a dia.

## O que você consegue fazer

- Ver desempenho de visualizações e ações no perfil
- Acompanhar palavras-chave e tendências
- Analisar avaliações e usar sugestão de resposta com IA (opcional)
- Ver posts recentes e desempenho
- Publicar novos posts direto pela plataforma
- Publicar posts com imagem por URL ou com upload do computador
- Fazer check de saúde do perfil
- Exportar relatório em PDF

## Comece em 5 minutos

1. Abra a plataforma no navegador (`http://localhost:8501`).
2. Clique em **Login with Google**.
3. Autorize acesso à conta do Google Business Profile.
4. Na barra lateral, escolha a empresa em **Select Business**.
5. Defina o período em **Start Date** e **End Date**.
6. Clique em **Fetch Data** para carregar os dados.
7. Navegue pelas abas: **Overview**, **Reviews**, **Posts**, **Health** e **Create Post**.

## Como usar cada aba

### 1) Overview

Use para entender desempenho geral do perfil.

Passo a passo:
1. Veja o gráfico **Performance Over Time**.
2. Marque/desmarque métricas em **Select Metrics to Display**.
3. Analise cards de resumo e distribuição por plataforma/dispositivo.
4. Confira palavras-chave em **Top Keywords** e **All Keywords**.

### 2) Reviews

Use para acompanhar reputação e atendimento.

Passo a passo:
1. Veja total de avaliações, respondidas e não respondidas.
2. Use o filtro: **All Reviews**, **Only Unanswered**, **Only Answered**.
3. Abra uma avaliação para ler detalhes.
4. Se quiser, clique em **Generate AI Reply** para sugestão de resposta.

### 3) Posts

Use para ver os posts já publicados e desempenho.

Passo a passo:
1. Abra **Post Performance** para visão geral.
2. Em **Recent Posts**, clique no item para ver texto, tipo e CTA.

### 4) Create Post

Use para publicar um novo post no Google Business Profile.

Passo a passo:
1. Escolha o tipo em **Post Type**:
- `STANDARD`
- `OFFER`
- `EVENT`
2. Defina **Language Code** (exemplo: `pt-BR`).
3. Escreva o texto no campo **Post Text**.
4. (Opcional) Ative **Include CTA** e preencha tipo e link.
5. Em **Image Source**, escolha uma opção:
- `None`
- `Image URL`
- `Upload from computer`
6. Clique em **Publish Now**.
7. Aguarde a confirmação de sucesso.

### 5) Health

Use para identificar melhorias práticas no perfil.

Passo a passo:
1. Abra a aba **Health**.
2. Veja os indicadores em **Fraco**, **Razoável** e **Bom**.
3. Leia cada recomendação para ajustar o perfil.

### Exportar PDF

1. Vá para a aba **Overview**.
2. Clique em **Generate PDF Report**.
3. Clique em **Download PDF** para baixar o arquivo.

## Como criar um post com foto do computador

1. Vá para **Create Post**.
2. Em **Image Source**, selecione **Upload from computer**.
3. Escolha uma imagem (`.png`, `.jpg`, `.jpeg`).
4. Preencha os demais campos do post.
5. Clique em **Publish Now**.
6. Espere a mensagem de sucesso.

## Termos simples (glossário rápido)

- **Location**: unidade/empresa cadastrada no Google Business Profile.
- **CTA**: botão de ação do post (ex.: Saiba mais, Comprar, Ligar).
- **Topic Type**: tipo do post (`STANDARD`, `OFFER`, `EVENT`).
- **Fetch Data**: botão para buscar dados atualizados da conta.
- **Scope**: permissão de acesso que o Google solicita no login.

## Problemas comuns e solução

### 1) “Minha empresa não aparece no Select Business”

- Confirme se você está logado com a conta Google correta.
- Verifique se essa conta tem acesso ao perfil da empresa no GBP.
- Faça logout/login novamente e tente **Fetch Data**.

### 2) “Erro de login”

- Feche a aba e abra novamente a plataforma.
- Refaça o login Google.
- Se continuar, peça para o suporte validar o arquivo de credencial.

### 3) “Não carrega dados ao clicar Fetch Data”

- Verifique conexão com internet.
- Confirme período de datas válido (início menor que fim).
- Tente novamente em alguns minutos (limite temporário de API pode ocorrer).

### 4) “Erro ao publicar post com imagem”

- Teste outra imagem com formato suportado (`png`, `jpg`, `jpeg`).
- Reduza o tamanho do arquivo da imagem.
- Se usar URL, confirme que começa com `http://` ou `https://`.

### 5) “Erro de permissão no Google”

- Sua conta pode não ter permissão suficiente naquele perfil.
- Solicite acesso ao administrador do GBP.
- Faça novo login após receber a permissão.

## Segurança e privacidade

Boas práticas importantes:
- Nunca compartilhe `client_secret.json`.
- Nunca publique chaves/API keys em grupos (WhatsApp, Slack, e-mail).
- Não envie prints mostrando tokens, chaves ou credenciais.
- Use contas oficiais da empresa para acesso ao GBP.

Checklist rápido:
1. Credenciais guardadas em local seguro.
2. Acesso liberado apenas para quem realmente usa.
3. Chave de IA tratada como informação sensível.
4. Revisão periódica de quem tem acesso à conta.

## Configuração técnica (para suporte)

Se você for do time técnico/suporte, use esta seção.

### Requisitos

- Python 3.10+
- Credenciais OAuth do Google Business Profile

### Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Credenciais

Use `.env` como configuração padrão e recomendada (baseado no `.env.example`):

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_AUTH_URI`
- `GOOGLE_TOKEN_URI`

Suporte legado/opcional continua disponível para:
- `client_secret.json` na raiz do projeto
- `.streamlit/secrets.toml` com objeto OAuth `web`

Escopo necessário:
- `https://www.googleapis.com/auth/business.manage`
- `https://www.googleapis.com/auth/drive.file`
- `https://www.googleapis.com/auth/drive.metadata.readonly`

### Chave de IA (opcional)

```bash
export GEMINI_API_KEY="sua_chave_aqui"
```

### Execução

```bash
streamlit run app.py
```

Abra em:
- `http://localhost:8501`

## Servidor MCP (Google Business Profile)

Há um servidor MCP fino que reutiliza `data_fetcher.py` e `drive_helper.py` e devolve só JSON (sem Streamlit, DataFrame, PDF ou Plotly).

```bash
python mcp_server.py
python mcp_server.py --http --port 8765
python mcp_server.py --oauth
```

Autenticação (não commitar): `access_token` na tool, `GOOGLE_ACCESS_TOKEN`, arquivo gitignored `.gmb-mcp-token.json`, ou as tools `start_oauth` / `complete_oauth`.

Exemplo Cursor (stdio):

```json
{
  "mcpServers": {
    "google-business-profile": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/caminho/absoluto/deste/repo",
      "env": {
        "GOOGLE_ACCESS_TOKEN": "<seu-token-oauth>"
      }
    }
  }
}
```

Tools de leitura: `list_accounts`, `list_locations`, `get_daily_metrics`, `get_search_keywords`, `list_reviews`, `list_posts`, `list_media`, `list_questions`, `profile_health_check`.

Tools de escrita: `create_local_post`, `upload_image_to_drive`, `reply_to_review`.

Detalhes em [README.md](README.md#mcp-server-google-business-profile).

## Desenvolvimento

Instale ferramentas de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Rode verificações:

```bash
ruff check src tests app.py auth.py mcp_server.py
pytest
python -m py_compile app.py auth.py data_fetcher.py drive_helper.py mcp_server.py
```

Scripts utilitários/debug ficam em `tools/`.

## Licença

MIT (veja `LICENSE`).
