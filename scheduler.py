from apscheduler.schedulers.background import BackgroundScheduler
from collector import collect_data
from datetime import datetime
import time

def safe_collect():
    # Um erro na coleta é só registrado; nunca derruba o app nem o agendador
    try:
        collect_data()
    except Exception as e:
        print(f"Erro na coleta agendada: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # next_run_time=agora: a primeira coleta roda logo após subir, em segundo
    # plano, sem bloquear a inicialização; depois repete a cada 30 minutos
    scheduler.add_job(safe_collect, "interval", minutes=30, next_run_time=datetime.now())
    scheduler.start()
    print("Agendador iniciado — primeira coleta agora, depois a cada 30 minutos.")
    return scheduler