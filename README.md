# 🌧️ Sistema de Monitoramento de Enchentes

Sistema IoT de monitoramento climático com análise de risco de enchentes em tempo real e alertas via Telegram, desenvolvido como projeto integrador universitário.

---

## 📡 Sobre o projeto

O sistema coleta automaticamente dados meteorológicos de oito cidades do interior de São Paulo (**Adamantina, Lucélia, Osvaldo Cruz, Bauru, São Carlos, Ribeirão Preto, Piracicaba e Borá**) por meio da API pública Open-Meteo (gratuita e sem chave de API), armazena as informações em um banco de dados e classifica o risco de enchente em três níveis. Os dados são exibidos em um painel web acessível por qualquer dispositivo, e quem se inscreve no bot do Telegram recebe um aviso sempre que o risco da sua cidade sobe.

O banco de dados já está preparado para receber, no futuro, leituras de um sensor físico próprio (qualidade do ar, temperatura e umidade), ao lado dos dados oficiais da Open-Meteo.

---

## ✨ Funcionalidades

- Coleta automática de dados climáticos (chuva, umidade e vento) de todas as cidades a cada 30 minutos — a primeira coleta roda em segundo plano logo após o servidor subir, sem travar a inicialização
- Seletor de cidade no painel (as rotas da API aceitam `?city=<slug>`; a lista fica em `/api/cities`; a cidade padrão é Osvaldo Cruz)
- Previsão horária de chuva para as próximas 12 horas (rota `/api/forecast`)
- Análise e classificação de risco em tempo real
- **Alertas por cidade** considerando chuva medida, previsão de chuva, chuva acumulada em 24h e vento
- **Bot do Telegram** ([@monitor_enchentes_bot](https://t.me/monitor_enchentes_bot)) para se inscrever em uma ou mais cidades e receber os alertas
- Painel web com tema escuro responsivo, gráfico de precipitação, histórico de registros e botão para receber alertas no Telegram
- Banner de alerta dinâmico com três níveis de risco
- Atualização automática do painel a cada 60 segundos

---

## 🚦 Níveis de risco

### Risco exibido no painel

Classificação de cada leitura com base na chuva medida no momento:

| Nível | Cor | Critério |
|---|---|---|
| Normal | 🟢 Verde | Precipitação < 5 mm/h |
| Atenção | 🟡 Amarelo | Precipitação entre 5 e 25 mm/h |
| Alerta Vermelho | 🔴 Vermelho | Precipitação > 25 mm/h |

### Critérios dos alertas (Telegram)

Os alertas usam critérios mais completos, baseados nos avisos do **INMET** (chuva acumulada em 24h e vento) e no gatilho de chuva horária do **Alerta Rio**. Um nível dispara se **qualquer** um dos critérios for atingido:

| Critério | 🟡 Atenção | 🔴 Alerta Vermelho |
|---|---|---|
| Chuva medida agora | ≥ 25 mm/h | ≥ 50 mm/h |
| Chuva prevista | ≥ 25 mm em 1 hora | ≥ 50 mm em 3 horas seguidas |
| Chuva acumulada nas últimas 24h | ≥ 50 mm | ≥ 100 mm |
| Vento medido agora | ≥ 50 km/h | ≥ 90 km/h |

Os limiares ficam centralizados em `ALERT_THRESHOLDS`, no arquivo `analyzer.py`, e podem ser ajustados à realidade local.

Regras de envio:

- O alerta só é enviado quando o nível **sobe** (Normal → Atenção → Alerta Vermelho); no mesmo nível ele não se repete
- Quando o nível baixa, o estado é atualizado sem aviso, para que uma nova subida volte a alertar
- No cálculo do acúmulo de 24h, cada leitura conta por no máximo 1 hora, para que uma pausa do servidor não infle o total
- Toda mensagem traz a orientação de procurar a Defesa Civil (199) e os canais oficiais em caso de emergência

---

## 🤖 Bot do Telegram

Acesse [@monitor_enchentes_bot](https://t.me/monitor_enchentes_bot) (ou o botão no painel) e use os comandos:

| Comando | Ação |
|---|---|
| `/start` | Escolher uma cidade para receber alertas |
| `/status` | Ver as cidades em que você está inscrito |
| `/parar` | Cancelar os alertas de uma cidade ou de todas |

O bot funciona apenas em conversas privadas e não pede número de telefone. Se um usuário bloquear o bot, suas inscrições são removidas automaticamente.

**Segurança do webhook:**

- O webhook só é ativado quando `TELEGRAM_WEBHOOK_SECRET` está definido; o caminho da rota é derivado desse segredo e não aparece no código
- Toda chamada precisa trazer o segredo no cabeçalho `X-Telegram-Bot-Api-Secret-Token`
- Limite de taxa: 20 mensagens por minuto por chat e 10 chamadas por minuto por IP sem o segredo válido (acima disso, resposta `429`)
- O token do bot nunca é gravado no código nem aparece nos logs

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python 3.13 | Linguagem principal |
| Flask | Framework web (backend) |
| SQLite | Banco de dados |
| APScheduler | Agendamento da coleta automática |
| Gunicorn | Servidor WSGI para produção |
| HTML + CSS + JavaScript | Interface do painel web |
| Chart.js | Gráfico de precipitação |
| Open-Meteo API | Fonte dos dados climáticos e da previsão |
| Telegram Bot API | Envio dos alertas e inscrição dos usuários |
| Render.com | Hospedagem online gratuita |
| GitHub | Versionamento de código |

---

## 📁 Estrutura do projeto

```
flood-monitor/
├── app.py              # Servidor Flask, rotas da API e webhook do Telegram
├── cities.py           # Lista central das cidades monitoradas
├── collector.py        # Coleta de dados da API climática
├── database.py         # Criação e gerenciamento do banco SQLite
├── analyzer.py         # Classificação de risco e limiares de alerta
├── alerts.py           # Decide quando alertar (e simulação de testes)
├── telegram_bot.py     # Bot do Telegram: comandos, inscrições e envio
├── ratelimit.py        # Limite de taxa em memória para o webhook
├── scheduler.py        # Agendador de coleta automática
├── requirements.txt    # Dependências do projeto
├── Procfile            # Configuração para deploy no Render
└── templates/
    └── index.html      # Painel web
```

---

## 🗄️ Banco de dados

O arquivo `flood_data.db` (SQLite) é criado automaticamente e possui três tabelas:

| Tabela | Conteúdo |
|---|---|
| `weather_data` | Histórico de leituras por cidade (chuva, umidade, vento, descrição e risco) |
| `alert_state` | Último nível de alerta notificado de cada cidade |
| `subscribers` | Inscrições do Telegram (um chat pode acompanhar várias cidades) |

A tabela `weather_data` registra a origem de cada leitura (`origem_dado`, hoje sempre `oficial`) e já contém colunas reservadas para o sensor físico: `id_dispositivo`, `ponto_instalacao`, `co2_ppm`, `pm1_0`, `pm2_5`, `pm10`, `temperatura_sensor`, `umidade_sensor` e `status_conexao`. Colunas novas são adicionadas a bancos antigos sem apagar o histórico.

---

## 🔄 Arquitetura do sistema

```
  Open-Meteo API
       ↓
  collector.py  ←  scheduler.py (a cada 30 min)
       ↓
  analyzer.py (classifica o risco)
       ↓
  database.py (SQLite)  ──→  alerts.py (o nível subiu?)
       ↓                          ↓
  app.py (Flask)            telegram_bot.py  ──→  inscritos no Telegram
       ↓                          ↑
  index.html (painel web)   webhook (/start, /status, /parar)
```

---

## ▶️ Como executar localmente

**Pré-requisitos:** Python 3.10 ou superior

```bash
# Clone o repositório
git clone https://github.com/loraadev/flood-monitor.git
cd flood-monitor

# Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Instale as dependências
pip install -r requirements.txt

# Execute o sistema (não é preciso configurar chave de API)
python app.py
```

Acesse em: `http://127.0.0.1:5000`

Sem as variáveis do Telegram, o painel e a coleta funcionam normalmente; apenas o webhook e o envio de alertas ficam desativados.

### Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `TELEGRAM_TOKEN` | Para alertas | Token do bot, fornecido pelo @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Para alertas | Segredo do webhook (1 a 256 caracteres: `A-Z`, `a-z`, `0-9`, `_` e `-`) |
| `FLASK_DEBUG` | Não | Use `1` para ativar o modo debug localmente |

### Configurar o webhook do Telegram

Com as variáveis definidas, rode uma única vez:

```bash
python telegram_bot.py set-webhook https://flood-monitor-v79c.onrender.com
python telegram_bot.py info  # confere a configuração
```

### Simular alertas

Para testar a lógica de alertas sem enviar mensagens reais (usa apenas cidades fictícias):

```bash
python alerts.py
```

---

## 🌐 Deploy

O sistema está hospedado gratuitamente no **Render.com** com deploy automático a cada push na branch `main`. As variáveis `TELEGRAM_TOKEN` e `TELEGRAM_WEBHOOK_SECRET` devem ser configuradas no painel do Render.

🔗 **Acesse o painel:** https://flood-monitor-v79c.onrender.com

🤖 **Bot do Telegram:** https://t.me/monitor_enchentes_bot

> O plano gratuito pode levar até 50 segundos para carregar após um período de inatividade.

---

## 📊 Fonte dos dados

Os dados climáticos são fornecidos pela [Open-Meteo](https://open-meteo.com/), gratuita para uso não comercial e sem necessidade de chave de API. A consulta é feita pela latitude e longitude de cada cidade, definidas em `cities.py`.

> ⚠️ Esta é uma ferramenta informativa. Em situações de emergência, procure a Defesa Civil (199) e os canais oficiais.

---

## 👩‍💻 Autora

Desenvolvido por **Gabriela C. Alencar** como projeto integrador universitário.
