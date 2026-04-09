# 🌧️ Sistema de Monitoramento de Enchentes

Sistema IoT de monitoramento climático com análise de risco de enchentes em tempo real, desenvolvido como projeto integrador universitário.

---

## 📡 Sobre o projeto

O sistema coleta automaticamente dados meteorológicos da cidade de **Osvaldo Cruz, SP** por meio de uma API pública, armazena as informações em um banco de dados e classifica o risco de enchente em três níveis. Os dados são exibidos em um painel web acessível por qualquer dispositivo.

---

## ✨ Funcionalidades

- Coleta automática de dados climáticos a cada 30 minutos
- Análise e classificação de risco em tempo real
- Painel web com gráfico de precipitação e histórico de registros
- Banner de alerta dinâmico com três níveis de risco
- Atualização automática do painel a cada 60 segundos

---

## 🚦 Níveis de risco

| Nível | Cor | Critério |
|---|---|---|
| Normal | 🟢 Verde | Precipitação < 5 mm/h |
| Atenção | 🟡 Amarelo | Precipitação entre 5 e 25 mm/h |
| Alerta Vermelho | 🔴 Vermelho | Precipitação > 25 mm/h |

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
| OpenWeatherMap API | Fonte dos dados climáticos |
| Render.com | Hospedagem online gratuita |
| GitHub | Versionamento de código |

---

## 📁 Estrutura do projeto

```
flood-monitor/
├── app.py              # Servidor Flask e rotas da API
├── collector.py        # Coleta de dados da API climática
├── database.py         # Criação e gerenciamento do banco SQLite
├── analyzer.py         # Regras de classificação de risco
├── scheduler.py        # Agendador de coleta automática
├── requirements.txt    # Dependências do projeto
├── Procfile            # Configuração para deploy no Render
└── templates/
    └── index.html      # Painel web
```

---

## 🔄 Arquitetura do sistema

```
OpenWeatherMap API
       ↓
  collector.py  ←  scheduler.py (a cada 30 min)
       ↓
  analyzer.py (classifica o risco)
       ↓
  database.py (SQLite)
       ↓
  app.py (Flask)
       ↓
  index.html (painel web)
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

# Configure sua chave da API no collector.py
# Substitua "SUA_CHAVE_AQUI" pela sua chave do OpenWeatherMap

# Execute o sistema
python app.py
```

Acesse em: `http://127.0.0.1:5000`

---

## 🌐 Deploy

O sistema está hospedado gratuitamente no **Render.com** com deploy automático a cada push na branch `main`.

🔗 **Acesse o painel:** https://flood-monitor-v79c.onrender.com

> O plano gratuito pode levar até 50 segundos para carregar após um período de inatividade.

---

## 📊 Fonte dos dados

Os dados climáticos são fornecidos pela [OpenWeatherMap API](https://openweathermap.org/api), plano gratuito, com até 1.000 requisições por dia.

---

## 👩‍💻 Autora

Desenvolvido por **Gabriela C. Alencar** como projeto integrador universitário.