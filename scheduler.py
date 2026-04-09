from apscheduler.schedulers.background import BackgroundScheduler
from collector import collect_data
import time

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(collect_data, "interval", minutes=30)
    scheduler.start()
    print("Agendador iniciado — coleta a cada 30 minutos.")
    return scheduler