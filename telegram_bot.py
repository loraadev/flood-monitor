import hashlib
import hmac
import os
import re
import sys
import requests
from datetime import datetime, timezone, timedelta
from cities import CITIES, get_city
from database import add_subscriber, get_subscriptions, get_subscribers, remove_subscription

# Token e segredo vêm só do ambiente; nunca ficam no código nem nos logs
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

DISCLAIMER = "Ferramenta informativa. Em emergência, procure a Defesa Civil (199) e os canais oficiais."
LEVEL_ICONS = {"Atenção": "🟡", "Alerta Vermelho": "🔴"}

fuso_brasilia = timezone(timedelta(hours=-3))

def _webhook_path():
    # Caminho não óbvio derivado do segredo: não aparece no código nem no repositório
    if not WEBHOOK_SECRET:
        return None
    digest = hashlib.sha256(("flood-monitor:" + WEBHOOK_SECRET).encode()).hexdigest()[:32]
    return f"/telegram/webhook/{digest}"

WEBHOOK_PATH = _webhook_path()

def check_webhook_secret(header_value):
    if not WEBHOOK_SECRET or not header_value:
        return False
    return hmac.compare_digest(header_value.encode(), WEBHOOK_SECRET.encode())

def _redact(text):
    # A URL da API contém o token; tira ele de qualquer mensagem de erro
    return str(text).replace(TOKEN, "***") if TOKEN else str(text)

def _call(method, payload):
    """Chama a API do Telegram. Devolve (status_code, json) ou (None, None) em falha de rede."""
    if not TOKEN:
        print(f"Telegram: TELEGRAM_TOKEN não configurado; '{method}' ignorado")
        return None, None
    try:
        response = requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=payload, timeout=10)
        try:
            body = response.json()
        except ValueError:
            body = {}
        if not body.get("ok"):
            print(f"Telegram: '{method}' falhou com {response.status_code}: {_redact(body.get('description', ''))}")
        return response.status_code, body
    except Exception as e:
        print(f"Telegram: erro de conexão em '{method}': {type(e).__name__}: {_redact(e)}")
        return None, None

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text[:4096]}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    status, _ = _call("sendMessage", payload)
    return status


# ---------------------------------------------------------------------
# Envio de alertas (chamado por alerts.py quando o nível de uma cidade sobe)
# ---------------------------------------------------------------------
def notify_city(city_name, level, message):
    city = next((c for c in CITIES if c["name"] == city_name), None)
    if city is None:
        return
    chat_ids = get_subscribers(city["slug"])
    if not chat_ids:
        return
    text = f"{LEVEL_ICONS.get(level, '')} {level} — {city['name']}\n\n{message}\n\n{DISCLAIMER}".strip()
    sent = removed = 0
    for chat_id in chat_ids:
        status = send_message(chat_id, text)
        if status == 200:
            sent += 1
        elif status == 403:
            # Usuário bloqueou o bot: remove a inscrição
            remove_subscription(chat_id)
            removed += 1
    print(f"Telegram: alerta de {city['name']} enviado para {sent} de {len(chat_ids)} inscrito(s); {removed} removido(s) por bloqueio")


# ---------------------------------------------------------------------
# Tratamento das mensagens recebidas pelo webhook
# ---------------------------------------------------------------------
def _city_keyboard(prefix):
    buttons = [{"text": c["name"], "callback_data": f"{prefix}:{c['slug']}"} for c in CITIES]
    return {"inline_keyboard": [buttons[i:i + 2] for i in range(0, len(buttons), 2)]}

def _city_names(slugs):
    return [get_city(s)["name"] for s in slugs if get_city(s)]

def _cmd_start(chat_id):
    send_message(
        chat_id,
        "Olá! Eu aviso quando o risco de chuva forte, alagamento ou vento forte subir na cidade que você escolher.\n\n"
        "Escolha uma cidade:",
        _city_keyboard("sub")
    )

def _cmd_status(chat_id):
    names = _city_names(get_subscriptions(chat_id))
    if not names:
        send_message(chat_id, "Você ainda não recebe alertas de nenhuma cidade. Use /start para escolher uma.")
    else:
        lista = "\n".join(f"• {n}" for n in names)
        send_message(chat_id, f"Você recebe alertas de:\n{lista}\n\nUse /parar para cancelar.")

def _cmd_parar(chat_id):
    slugs = [s for s in get_subscriptions(chat_id) if get_city(s)]
    if not slugs:
        send_message(chat_id, "Você não tem inscrições ativas.")
    elif len(slugs) == 1:
        remove_subscription(chat_id)
        send_message(chat_id, f"Pronto, você não vai mais receber alertas de {get_city(slugs[0])['name']}.")
    else:
        buttons = [[{"text": get_city(s)["name"], "callback_data": f"unsub:{s}"}] for s in slugs]
        buttons.append([{"text": "Todas as cidades", "callback_data": "unsub:*"}])
        send_message(chat_id, "De qual cidade você quer parar de receber alertas?", {"inline_keyboard": buttons})

def _cmd_help(chat_id):
    send_message(chat_id, "Comandos:\n/start — escolher uma cidade\n/status — ver suas inscrições\n/parar — cancelar alertas")

def _handle_message(message):
    chat = message.get("chat")
    if not isinstance(chat, dict) or chat.get("type") != "private":
        return  # só conversas privadas
    chat_id = chat.get("id")
    text = message.get("text")
    if not isinstance(chat_id, int) or not isinstance(text, str):
        return
    # "/start@monitor_enchentes_bot payload" -> "/start"
    command = text.strip()[:64].split(" ")[0].split("@")[0].lower()
    if command == "/start":
        _cmd_start(chat_id)
    elif command == "/status":
        _cmd_status(chat_id)
    elif command == "/parar":
        _cmd_parar(chat_id)
    else:
        _cmd_help(chat_id)

def _handle_callback(callback):
    callback_id = callback.get("id")
    if isinstance(callback_id, str):
        # O Telegram pede uma resposta a todo clique em botão
        _call("answerCallbackQuery", {"callback_query_id": callback_id})
    message = callback.get("message")
    data = callback.get("data")
    if not isinstance(message, dict) or not isinstance(data, str):
        return
    chat = message.get("chat")
    if not isinstance(chat, dict) or chat.get("type") != "private" or not isinstance(chat.get("id"), int):
        return
    chat_id = chat["id"]
    match = re.fullmatch(r"(sub|unsub):([a-z0-9-]{1,40}|\*)", data)
    if not match:
        return
    action, slug = match.groups()

    if action == "unsub" and slug == "*":
        remove_subscription(chat_id)
        send_message(chat_id, "Pronto, você não vai mais receber alertas de nenhuma cidade.")
        return
    city = get_city(slug)
    if city is None:
        return
    if action == "sub":
        created_at = datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M")
        if add_subscriber(chat_id, slug, created_at):
            send_message(chat_id, f"Pronto! Você vai receber alertas de {city['name']} quando o risco subir.\n\n"
                                  f"Use /status para ver suas inscrições e /parar para cancelar.\n\n{DISCLAIMER}")
        else:
            send_message(chat_id, f"Você já recebe alertas de {city['name']}.")
    else:
        remove_subscription(chat_id, slug)
        send_message(chat_id, f"Pronto, você não vai mais receber alertas de {city['name']}.")

def update_chat_id(update):
    """chat_id de quem enviou a mensagem ou clicou no botão, ou None."""
    if not isinstance(update, dict):
        return None
    message = update.get("message")
    if not isinstance(message, dict):
        callback = update.get("callback_query")
        message = callback.get("message") if isinstance(callback, dict) else None
    chat = message.get("chat") if isinstance(message, dict) else None
    chat_id = chat.get("id") if isinstance(chat, dict) else None
    return chat_id if isinstance(chat_id, int) else None

def handle_update(update):
    if not isinstance(update, dict):
        return
    if isinstance(update.get("message"), dict):
        _handle_message(update["message"])
    elif isinstance(update.get("callback_query"), dict):
        _handle_callback(update["callback_query"])


# ---------------------------------------------------------------------
# Configuração do webhook (rodar uma vez, com as variáveis de ambiente)
#   python telegram_bot.py set-webhook https://flood-monitor-v79c.onrender.com
#   python telegram_bot.py info
# ---------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "set-webhook":
        if not TOKEN or not WEBHOOK_SECRET:
            sys.exit("Defina TELEGRAM_TOKEN e TELEGRAM_WEBHOOK_SECRET antes.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", WEBHOOK_SECRET):
            sys.exit("TELEGRAM_WEBHOOK_SECRET deve ter 1-256 caracteres, só A-Z, a-z, 0-9, _ e -.")
        status, body = _call("setWebhook", {
            "url": sys.argv[2].rstrip("/") + WEBHOOK_PATH,
            "secret_token": WEBHOOK_SECRET,
            "allowed_updates": ["message", "callback_query"],
            "drop_pending_updates": True
        })
        print(status, body)
    elif len(sys.argv) == 2 and sys.argv[1] == "info":
        status, body = _call("getWebhookInfo", {})
        print(status, body)
    else:
        print("Uso: python telegram_bot.py set-webhook <url-base> | info")
