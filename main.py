from datetime import datetime, timedelta
import json
import logging
import math
import colorlog
from dateutil.relativedelta import relativedelta
import pytz
from telegram import ReplyKeyboardMarkup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, filters, MessageHandler, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import entrate
import errors
from entrate import Entrate

import migrations
import spese
from spese import Spesa
import db
TOKEN_API = '7101960618:AAFdwl7hm7LSO9cbNY40JG6h19bSgEW5eX8'
user_data = {}
TZ = pytz.timezone('Europe/Rome')
COMMANDS = {"start" : "Crea l'utente",
            "saldo" : "Visualizza il saldo previsto",
            "speseVarie" : "Visualizza la somma delle spese",
            "addebitoCc" : "Visualizza il prossimo addebito della carta dui credito",
            "sommaSpese" : "Visualizza la somma delle spese",
            "add" : "Aggiungi un entrata",
            "addSpesa" : "Aggiungi una spesa",
            "addSpesaCc" : "Aggiungi una spesa per la carta di credito",
            "report" : "Visualizza il report mensile",
            "help" : "Visualizza tutti i comandi"

}

# Crea logger
formatter = colorlog.ColoredFormatter(
"%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
log_colors={
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
    },
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger("color_logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

STATO1,STATO2,STATO3,STATO4 = range(4)

async def crea_utente(update: Update, context: CallbackContext):
    utente = update.message.from_user.username
    try:
        db.create(utente)
        await update.message.reply_text(f"Utente {utente} creato")
        logger.info(f" {update.message.from_user.username} | Utente {utente} creato")
    except errors.CreateUserError as e:
        await update.message.reply_text(f"{e}")
        logger.error(f" {update.message.from_user.username} | {e}")
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.error(f" {update.message.from_user.username} | {e}")

async def get_spesa(update: Update, context: CallbackContext):
    try:
        
        await update.message.reply_text("Vuoi ricercare per un intervallo oppure per gli ultimi 30 giorni?")
        reply_keyboard = [['Intervallo', 'Mensile']]
        await update.message.reply_text("Scegli un'opzione", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")

async def get_spesa_secondo_stato(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        reply = update.message.text
        if reply == "Intervallo":
            await update.message.reply_text("Inserisci la data di inizio (gg/mm/aaaa)")
            return STATO2
        else:
            out = ''
            fine = datetime.now(TZ)
            inizio = (datetime.now(TZ) - timedelta(days=30))
            spese = db.get_spesa(utente, fine,inizio)
            try:
                if fine.day < 8:
                    spese_cc = db.get_addebito(utente, (fine.month))
                else: 
                    spese_cc = db.get_addebito(utente, (fine.month+1)%12)
                spese.append(spese_cc)
                spese.sort(key=lambda x: x.timestamp)
            except errors.NoAddebitoError:
                spese_cc = None
            if spese == [] and spese_cc == None:
                await update.message.reply_text("Nessuna spesa trovata")
                return ConversationHandler.END
            for spesa in spese:
                if spesa.descrizione == "Totale":
                    totale = spesa
                    if spese_cc != None:
                        totale.importo += spese_cc.importo
                else:   
                    out += f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€\n"
            out += f"Totale spese: {totale.importo}€"
            await update.message.reply_text(f"Spese:\n {out}")
            logger.info(f"{update.message.from_user.username} | 200: Spese trovate")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.info(f"{update.message.from_user.username} | 500: Errore {e}")

async def get_spesa_terzo_stato(update: Update, context: CallbackContext):
    try:
        try:
            giorno, mese, anno = update.message.text.split("/")
        except:
            await update.message.reply_text("Formato non valido, riprova")
            return STATO2
        data = f"{anno}/{mese}/{giorno} 00:00:00"
        context.user_data['inizio'] = data
        await update.message.reply_text("Inserisci la data di fine (gg/mm/aaaa), scrivi 'x' per la data attuale")
        return STATO3
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.info(f"{update.message.from_user.username} | 500: Errore {e}")

async def get_spesa_quarto_stato(update: Update, context: CallbackContext):
    try:
        if update.message.text == 'x':
            data = datetime.now(TZ)
        else:
            try:
                
                giorno, mese, anno = update.message.text.split("/")
                data = datetime(int(anno), int(mese), int(giorno),0,0,0)
            except:
                await update.message.reply_text("Formato non valido, riprova")
                return STATO3
        
        context.user_data['fine'] = data
        utente = update.message.from_user.username
        out = ''
        spese = db.get_spesa(utente, context.user_data['fine'], context.user_data['inizio'])
        spese_cc = db.get_spesa_cc_date(utente, context.user_data['fine'], context.user_data['inizio'])
        if spese == []:
            await update.message.reply_text("Nessuna spesa trovata")
            return ConversationHandler.END
        for spesa in spese:
            if spesa.descrizione == "Totale":
                totale = spesa
                break
            out += f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€\n"
        out += "Spese carta di credito:\n"
        for spesa_cc in spese_cc:
            out += f"{spesa_cc.descrizione} | {spesa_cc.timestamp} | Importo: {spesa_cc.importo}€ | Mensilità: {spesa_cc.mensilità} | Rata: {round(spesa_cc.importo/spesa_cc.mensilità,2)}\n"
            totale.importo += spesa_cc.importo
        out += f"Totale spese: {totale.importo}€"
        logger.info(out)
        await update.message.reply_text(f"Spese:\n {out}")
        logger.info(f"{update.message.from_user.username} | 200: Spese trovate")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")

async def add_spesa(update: Update, context: CallbackContext):
    try:
        logger.info(f"{update.message.from_user.username} | Richiesta add spesa")
        await update.message.reply_text("Inserisci la descrizione della spesa")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def add_spesa_state2(update: Update, context: CallbackContext):
    try:
        context.user_data['descrizione'] = update.message.text
        await get_budget(update, context)
        await update.message.reply_text("Inserisci l'importo della spesa") 
        return STATO2
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}") 
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def add_spesa_state3(update: Update, context: CallbackContext):
    try:
        ts = datetime.now(TZ)
        context.user_data['importo'] = update.message.text
        db.salva_spesa(update.message.from_user.username, context.user_data['descrizione'], context.user_data['importo'], ts)
        await update.message.reply_text("Spesa salvata")
        await get_budget(update, context)
        logger.info(f"{update.message.from_user.username} | 201: Spesa salvata")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")

async def add_entrata(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Inserisci la descrizione dell'entrata")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")        
async def add_entrata_state2(update: Update, context: CallbackContext):
    try:
        context.user_data['descrizione'] = update.message.text
        await update.message.reply_text("Inserisci l'importo dell'entrata")
        return STATO2
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def add_entrata_state3(update: Update, context: CallbackContext):
    try:
        ts = datetime.now(TZ)
        context.user_data['importo'] = update.message.text
        db.salva_entrata(update.message.from_user.username, context.user_data['descrizione'], context.user_data['importo'], ts)
        await update.message.reply_text("Entrata salvata")
        print(f"{ts} | {update.message.from_user.username} | 201: Entrata salvata")
        return ConversationHandler.END
    except Exception as e: 
        await update.message.reply_text(f"Errore, riprova \n{e}")
        print (f"{ts} | {update.message.from_user.username} | 500: Errore {e}")

async def get_entrate(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Vuoi ricercare per un intervallo oppure per gli ultimi 30 giorni?")
        reply_keyboard = [['Intervallo', 'Mensile']]
        await update.message.reply_text("Scegli un'opzione", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        logger.info(f"{update.message.from_user.username} | Richiesta get entrate")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def get_entrate_secondo_stato(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        reply = update.message.text
        if reply == "Intervallo":
            await update.message.reply_text("Inserisci la data di inizio (gg/mm/aaaa)")
            return STATO2
        else:
            out = ''
            fine = datetime.now(TZ).strftime("%Y/%m/%d %H:%M:%S")
            inizio = (datetime.now(TZ) - timedelta(days=30)).strftime("%Y/%m/%d %H:%M:%S")
            entrate = db.get_entrata(utente, fine,inizio)
            if entrate == []:
                await update.message.reply_text("Nessuna entrata trovata")
                return ConversationHandler.END
            for entrata in entrate:
                out += f"{entrata.descrizione} | {entrata.timestamp} | Importo: {entrata.importo}€\n"
            await update.message.reply_text(f"Entrate:\n {out}")
            logger.info(f"{update.message.from_user.username} | 200: Entrate trovate")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def get_entrate_terzo_stato(update: Update, context: CallbackContext):
    try:
        try:
            giorno, mese, anno = update.message.text.split("/")
        except:
            await update.message.reply_text("Formato non valido, riprova")
            return STATO2
        data = f"{anno}/{mese}/{giorno} 00:00:00"
        context.user_data['inizio'] = data
        await update.message.reply_text("Inserisci la data di fine (gg/mm/aaaa), scrivi 'x' per la data attuale")
        return STATO3
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def get_entrate_quarto_stato(update: Update, context: CallbackContext):
    try:
        if update.message.text == 'x':
            data = datetime.now(TZ).strftime("%Y/%m/%d %H:%M:%S")
        else:
            try:
                giorno, mese, anno = update.message.text.split("/")
                data = f"{anno}/{mese}/{giorno} 00:00:00"
            except:
                await update.message.reply_text("Formato non valido, riprova")
                return STATO3
        
        context.user_data['fine'] = data
        utente = update.message.from_user.username
        out = ''
        entrate = db.get_entrata(utente, context.user_data['fine'], context.user_data['inizio'])
        if entrate == []:
            await update.message.reply_text("Nessuna entrata trovata")
            return ConversationHandler.END
        for entrata in entrate:
            out += f"{entrata.descrizione} | {entrata.timestamp} | Importo: {entrata.importo}€\n"
        await update.message.reply_text(f"Entrate:\n {out}")
        logger.info(f"{update.message.from_user.username} | 200: Entrate trovate")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}") 
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
 
    
async def cancel(update: Update, context):
    """Interrompe la conversazione."""
    await update.message.reply_text("Operazione annullata.")
    logger.warning(f"{update.message.from_user.username} | 400: Operazione annullata")
    context.user_data.clear()
    return ConversationHandler.END

async def debug(update: Update, context: CallbackContext):
    await update.message.reply_text(f"{context.user_data}")

async def get_saldo(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        saldo = db.get_saldo(utente)
        await update.message.reply_text(f"Saldo il prossimo 8 del mese: {round(saldo,2)} Euro")
        logger.info(f"{update.message.from_user.username} | 200: Saldo trovato")
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
        
async def add_spesa_cc(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Inserisci la descrizione della spesa")
        logger.info(f"{update.message.from_user.username} | Richiesta add spesa cc")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def add_spesa_cc_state2(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        budget = db.get_budget(utente)
        context.user_data['descrizione'] = update.message.text
        if datetime.now(TZ).day < 8:
            if datetime.now(TZ).month == 1:
                inizio = datetime(datetime.now(TZ).year-1, 12, 8,0,0,0)
                fine =datetime(datetime.now(TZ).year, 1, 8,0,0,0)
            else:
                inizio = datetime(datetime.now(TZ).year, datetime.now(TZ).month-1, 8,0,0,0)
                fine = datetime(datetime.now(TZ).year, datetime.now(TZ).month, 8,0,0,0)
        else:
            if datetime.now(TZ).month == 12:
                inizio = datetime(datetime.now(TZ).year,12,8,0,0,0)
                fine = datetime(datetime.now(TZ).year+1, 1, 8,0,0,0)
            else:
                inizio = datetime(datetime.now(TZ).year, datetime.now(TZ).month, 8,0,0,0)
                fine = datetime(datetime.now(TZ).year, datetime.now(TZ).month+1, 8,0,0,0)
        spese_mensili = db.get_spesa(utente, fine, inizio)
        totale = spese_mensili[-1]
        if budget == None:
            await update.message.reply_text("Budget non impostato, clicca su /setbudget per impostarlo")
        elif totale.importo > budget:
            await update.message.reply_text(f"ATTENZIONE! Hai superato il budget mensile di {totale.importo - budget} Euro")
        else:
            await update.message.reply_text(f"A fronte di una spesa di {round(totale.importo,2)} Euro, questo mese puoi spendere ancora {round(budget-totale.importo, 2)} Euro")
        
        await update.message.reply_text("Inserisci l'importo della spesa")
        return STATO2
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def add_spesa_cc_state3(update: Update, context: CallbackContext):
    try:
        ts = datetime.now(TZ).strftime("%Y/%m/%d %H:%M:%S")
        context.user_data['importo'] = update.message.text
        await update.message.reply_text("Hai effettuato un pagamento a rate?")
        reply_keyboard = [['Si', 'No']]
        await update.message.reply_text("Scegli un'opzione", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return STATO3
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def add_spesa_cc_state4(update: Update, context: CallbackContext):
    try:
        if update.message.text == 'Si':
            await update.message.reply_text("Inserisci il numero di rate")
            return STATO4
        else:
            db.add_spesa_cc(update.message.from_user.username, float(context.user_data['importo']), context.user_data['descrizione'], datetime.now(TZ).strftime("%Y/%m/%d %H:%M:%S"), 1)
            await update.message.reply_text("Spesa salvata")
            await get_budget(update, context)
            logger.info(f"{update.message.from_user.username} | 201: Spesa salvata")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")    
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
async def add_spesa_cc_state5(update: Update, context: CallbackContext):
    try:
        rate = int(update.message.text)
        if rate > 13 or rate < 1:
            await update.message.reply_text("Numero di rate non valido, riprova")
            return STATO4
        db.add_spesa_cc(update.message.from_user.username, float(context.user_data['importo']), context.user_data['descrizione'],  datetime.now(TZ).strftime("%Y/%m/%d %H:%M:%S"), rate)
        await update.message.reply_text("Spesa salvata")
        await get_budget(update, context)
        logger.info(f"{update.message.from_user.username} | 201: Spesa salvata")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")   
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
    

async def get_spese_cc(update: Update, context: CallbackContext):
    try:
        tot = 0
        utente = update.message.from_user.username
        fine = datetime.now(TZ) - timedelta(days=365)
        spese = db.get_spesa_cc_date(utente, datetime.now(TZ), fine)
        out = ''
        for spesa in spese:
            if spesa.descrizione == "Totale":
                break
            ts_spesa = spesa.timestampd
            end = ts_spesa + relativedelta(months=spesa.mensilità)
            accredito = datetime.now(TZ) + relativedelta(months=1)
            accredito = datetime(accredito.year, accredito.month, 5,0,0,0)
            if end.month >= accredito.month:
                out += f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€ | Mensilita: {spesa.mensilità} | Rata: {round(spesa.importo/spesa.mensilità,2)}\n"
                tot += spesa.importo
        out += f"Totale spese: {tot}€"
        await update.message.reply_text(f"Spese:\n {out}")
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova\n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")


async def set_budget(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Inserisci il budget mensile")
        logger.info(f"{update.message.from_user.username} | Richiesta set budget")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")       
async def set_budget_state2(update: Update, context: CallbackContext):
    try:
        budget = update.message.text
        db.set_budget(update.message.from_user.username, budget)
        await update.message.reply_text("Budget salvato")
        logger.info(f"{update.message.from_user.username} | 201: Budget salvato")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")

async def get_budget(update: Update, context: CallbackContext):
    try:
        logger.info(f"{update.message.from_user.username} | Richiesta get budget")
        utente = update.message.from_user.username
        budget = db.get_budget(utente)
        if budget == None:
            logger.warning(f"{update.message.from_user.username} | 404: Budget non impostato")
            await update.message.reply_text("Budget non impostato, clicca su /setbudget per impostarlo")
            return ConversationHandler.END
        await update.message.reply_text(f"Budget mensile: {budget} Euro")
        
        # Trovo l'addebito della carta di credito
        try:
            addebito = spese.Spesa(0,"Addebito")
            now = datetime.now(TZ)
            if now.day < 8:
                mese = now.month
            else:
                mese = (now.month + 1) % 12
            addebito = db.get_addebito(utente,mese)
        except errors.NoAddebitoError:
            addebito.importo = 0
        except Exception as e2:
            await update.message.reply_text(f"Errore, riprova {e2}")
            logger.error(f"{update.message.from_user.username} | 500: Errore {e2}")
            return ConversationHandler.END
        finally: 
            
        
            #calcolo budget mensile
            if datetime.now(TZ).day < 8:
                if datetime.now(TZ).month == 1:
                    inizio = datetime(datetime.now(TZ).year-1, 12, 8,0,0,0)
                    fine =datetime(datetime.now(TZ).year, 1, 8,0,0,0)
                else:
                    inizio = datetime(datetime.now(TZ).year, datetime.now(TZ).month-1, 8,0,0,0)
                    fine = datetime(datetime.now(TZ).year, datetime.now(TZ).month, 8,0,0,0)
            else:
                if datetime.now(TZ).month == 12:
                    inizio = datetime(datetime.now(TZ).year,12,8,0,0,0)
                    fine = datetime(datetime.now(TZ).year+1, 1, 8,0,0,0)
                else:
                    inizio = datetime(datetime.now(TZ).year, datetime.now(TZ).month, 8,0,0,0)
                    fine = datetime(datetime.now(TZ).year, datetime.now(TZ).month+1, 8,0,0,0)
            spese_mensili = db.get_spesa(utente, fine, inizio)
            totale = spese_mensili[-1]
            if totale.importo > budget:
                await update.message.reply_text(f"ATTENZIONE! Hai superato il budget mensile di {totale.importo - budget} Euro. \n Il budget mensile è di {budget} Euro")
            else:
                await update.message.reply_text(f"A fronte di una spesa di {round(totale.importo,2)} Euro, questo mese puoi spendere ancora {round(budget-totale.importo, 2)} Euro")
            inizio = TZ.localize(inizio)
            fine = TZ.localize(fine)
            budget = budget - addebito.importo
            
            #calcolo budget settimanale
            delta_days = fine -  datetime.now(TZ)
            settimane_rimanenti = math.ceil(delta_days.days/7)
            inizio_oggi = datetime(datetime.now(TZ).year, datetime.now(TZ).month, datetime.now(TZ).day,0,0,0)
            inizio_oggi = TZ.localize(inizio_oggi)
            inizio_settimana = inizio_oggi - timedelta(days=delta_days.days%7)
            spesa_precedente = db.get_spesa(utente, inizio_settimana, inizio)[-1].importo
            budget_settimanale_rimanente = round((budget - spesa_precedente ) / settimane_rimanenti,2)
            fine_settimana = inizio_oggi + timedelta(days=7 - (delta_days.days%7))
            spesa_settimanale = db.get_spesa(utente, fine_settimana, inizio_settimana)
            '''if spesa_settimanale[-1].importo > budget_settimanale_rimanente:
                await update.message.reply_text(f"ATTENZIONE! Hai superato il budget settimanale di {round(spesa_settimanale[-1].importo - budget_settimanale_rimanente)} Euro per la settimana che va dal {inizio_settimana} al {fine_settimana}\n Il budget settimanale è di {budget_settimanale_rimanente} Euro")
            else:
                await update.message.reply_text(f"Con un budget settimanale di: {budget_settimanale_rimanente} Euro per la settimana che va dal {inizio_settimana.date().strftime("%d-%m-%Y")} al {fine_settimana.date().strftime("%d-%m-%Y")}\nA fronte di una spesa di {round(spesa_settimanale[-1].importo,2)} Euro, questa settimana puoi spendere ancora {round(budget_settimanale_rimanente - spesa_settimanale[-1].importo,2)} Euro.")
                '''

            
            #calcolo budget giornaliero
            domani = inizio_oggi + timedelta(days=1)
            spesa_giornaliera = db.get_spesa(utente, domani, inizio_oggi)
            spesa_precedente = db.get_spesa(utente, inizio_oggi, inizio)
            giorni_rimanenti = (fine - inizio_oggi).days
            budget_giornaliero = round((budget - spesa_precedente[-1].importo)/giorni_rimanenti,2)
            if spesa_giornaliera[-1].importo > budget_giornaliero:
                await update.message.reply_text(f"ATTENZIONE! Hai superato il budget giornaliero di {round(spesa_giornaliera[-1].importo - budget_giornaliero,2)} Euro. \n Il budget giornaliero è di {budget_giornaliero} Euro")
            else:
                await update.message.reply_text(f"A fronte di una spesa di {round(spesa_giornaliera[-1].importo,2)} Euro, oggi puoi spendere ancora {round(budget_giornaliero-spesa_giornaliera[-1].importo,2)} Euro")        
        logger.info(f"{update.message.from_user.username} | 200: Budget trovato")
    except Exception as e:
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")
        await update.message.reply_text(f"Errore, riprova {e}")


async def delete_spesa(update: Update, context: CallbackContext):
    try:
        context.user_data['utente'] = update.message.from_user.username
        spese = db.get_spesa(update.message.from_user.username,datetime.now(TZ), datetime(1900,1,1,0,0,0))
        spese.sort(key=lambda x: x.timestamp, reverse=True)
        context.user_data['spese'] = spese
        
        try:
            if context.user_data['contatore'] == None:
                context.user_data['contatore'] = 1
                
        except:
            context.user_data['contatore'] = 1
            await update.message.reply_text("Quali spese vuoi eliminare?")
        
        spese = context.user_data['spese']
        contatore = 0
        while contatore < 5:
            if context.user_data['contatore'] == len(spese):
                break
            spesa = spese[context.user_data['contatore']]
            context.user_data['contatore'] += 1
            contatore += 1
            keyboard = [InlineKeyboardButton("Elimina🗑️", callback_data=f"deletespesa {spesa.id}")]
            reply_markup = InlineKeyboardMarkup([keyboard])
            await update.message.reply_text(f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€", reply_markup=reply_markup)
        if context.user_data['contatore'] < len(spese):
            reply_keyboard = [["Vedi le prossime 5 spese"]]
           
            await update.message.reply_text("Vuoi vedere le prossime 5 spese?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return STATO1        
    
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
async def delete_spesa_state2(update: Update, context: CallbackContext):
    return ConversationHandler.END
  
async def delete_entrata(update: Update, context: CallbackContext):
    try:
        context.user_data['utente'] = update.message.from_user.username
        entrate = db.get_entrata(update.message.from_user.username,datetime.now(TZ), datetime(1900,1,1,0,0,0))
        entrate.sort(key=lambda x: x.timestamp, reverse=True)
        context.user_data['entrate'] = entrate
        
        try:
            if context.user_data['contatore'] == None:
                context.user_data['contatore'] = 1
                
        except:
            context.user_data['contatore'] = 1
            await update.message.reply_text("Quali entrate vuoi eliminare?")
        
        entrate = context.user_data['entrate']
        contatore = 0
        while contatore < 5:
            if context.user_data['contatore'] == len(entrate) -1:
                break
            entrata = entrate[context.user_data['contatore']]
            context.user_data['contatore'] += 1
            contatore += 1
            keyboard = [InlineKeyboardButton("Elimina🗑️", callback_data=f"deleteentrata {entrata.id}")]
            reply_markup = InlineKeyboardMarkup([keyboard])
            await update.message.reply_text(f"{entrata.descrizione} | {entrata.timestamp} | Importo: {entrata.importo}€", reply_markup=reply_markup)
        if context.user_data['contatore'] < len(entrate)-1:
            reply_keyboard = [["Vedi le prossime 5 entrate"]]
           
            await update.message.reply_text("Vuoi vedere le prossime 5 entrate?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return STATO1        
    
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")

async def edit_spesa(update: Update, context: CallbackContext):
    try:
        context.user_data['utente'] = update.message.from_user.username
        spese = db.get_spesa(update.message.from_user.username,datetime.now(TZ), datetime(1900,1,1,0,0,0))
        spese.sort(key=lambda x: x.timestamp, reverse=True)
        context.user_data['spese'] = spese
        
        try:
            if context.user_data['contatore'] == None:
                context.user_data['contatore'] = 1
                
        except:
            context.user_data['contatore'] = 1
            await update.message.reply_text("Quali spese vuoi eliminare?")
        
        spese = context.user_data['spese']
        contatore = 0
        while contatore < 5:
            if context.user_data['contatore'] == len(spese) -1:
                break
            spesa = spese[context.user_data['contatore']]
            context.user_data['contatore'] += 1
            contatore += 1
            keyboard = [InlineKeyboardButton("Elimina🗑️", callback_data=f"editspesa {spesa.id}")]
            reply_markup = InlineKeyboardMarkup([keyboard])
            await update.message.reply_text(f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€", reply_markup=reply_markup)
        if context.user_data['contatore'] < len(spese)-1:
            reply_keyboard = [["Vedi le prossime 5 spese"]]
           
            await update.message.reply_text("Vuoi vedere le prossime 5 spese?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return STATO1 
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")

async def edit_spesa_state2(update: Update, context: CallbackContext):
    try:
        importo = update.message.text
        spesa = db.modifica_spesa(context.user_data['utente'], context.user_data['spesa_id'], importo)      
        await update.message.reply_text(f"Spesa modificata\n Descrizione: {spesa.descrizione} | Importo: {spesa.importo}€")
        logger.info(f"{update.message.from_user.username} | 201: Spesa {context.user_data['spesa_id']} modificata")
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        logger.error(f"{update.message.from_user.username} | 500: Errore {e}")    

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Risponde alla callback per evitare il messaggio "pensieroso"
    if query.data.startswith("deletespesa"):
        spesa_id = query.data.split()[1]
        try:
            db.delete_spesa(query.from_user.username ,spesa_id)
        
            # Modifica il messaggio originale per indicare che la spesa è stata eliminata
            await query.message.reply_text("✅ Spesa eliminata con successo!")

            logger.info(f"{query.from_user.username} | 201: Spesa eliminata")
            context.user_data['contatore'] = 1
            context.user_data.clear()
            return ConversationHandler.END
        except errors.DeleteError as e:
            await query.message.edit_text(f"Errore, riprova {e}")
            logger.error(f"{query.from_user.username} | 500: Errore {e}")
        except  Exception as e:
            await query.message.edit_text(f"Errore, riprova {e}")
            logger.error(f"{query.from_user.username} | 500: Errore {e}")
    elif query.data.startswith("deleteentrata"):
        entrata_id = query.data.split()[1]
        try:
            db.delete_entrata(query.from_user.username ,entrata_id)
        
            # Modifica il messaggio originale per indicare che la spesa è stata eliminata
            await query.message.reply_text("✅ Entrata eliminata con successo!")

            logger.info(f"{query.from_user.username} | 201: Entrata eliminata")
            context.user_data['contatore'] = 1
            context.user_data.clear()
            return ConversationHandler.END
        except errors.DeleteError as e:
            await query.message.edit_text(f"Errore, riprova {e}")
            logger.error(f"{query.from_user.username} | 500: Errore {e}")
        except  Exception as e:
            await query.message.edit_text(f"Errore, riprova {e}")
            logger.error(f"{query.from_user.username} | 500: Errore {e}")
    elif query.data.startswith("deletespesacc"):
        spesa_id = query.data.split()[1]
        try:
            db.delete_spesa_cc(query.from_user.username ,spesa_id)
        
            # Modifica il messaggio originale per indicare che la spesa è stata eliminata
            await query.message.reply_text("✅ Spesa eliminata con successo!")

            logger.info(f"{query.from_user.username} | 201: Spesa eliminata")
            context.user_data['contatore'] = 1
            context.user_data.clear()
            return ConversationHandler.END
        except errors.DeleteError as e:
            await query.message.edit_text(f"Errore, riprova {e}")
            logger.error(f"{query.from_user.username} | 500: Errore {e}")
        except  Exception as e:
            await query.message.edit_text(f"Errore, riprova {e}")
            logger.error(f"{query.from_user.username} | 500: Errore {e}")
    elif query.data.startswith("editspesa"):
        spesa_id = query.data.split()[1]
        context.user_data['spesa_id'] = spesa_id
        await query.message.reply_text("Inserisci il nuovo importo")
        return STATO2
async def delete_spesa_cc(update: Update, context: CallbackContext):
    try:
        context.user_data['utente'] = update.message.from_user.username
        spese = db.get_spesa_cc_date(update.message.from_user.username,datetime.now(TZ), datetime(1900,1,1,0,0,0))
        spese.sort(key=lambda x: x.timestamp, reverse=True)
        context.user_data['spese'] = spese
        
        try:
            if context.user_data['contatore'] == None:
                context.user_data['contatore'] = 1
                
        except:
            context.user_data['contatore'] = 1
            await update.message.reply_text("Quali spese vuoi eliminare?")
        
        spese = context.user_data['spese']
        contatore = 0
        while contatore < 5:
            if context.user_data['contatore'] == len(spese) -1:
                break
            spesa = spese[context.user_data['contatore']]
            context.user_data['contatore'] += 1
            contatore += 1
            keyboard = [InlineKeyboardButton("Elimina🗑️", callback_data=f"deletespesacc {spesa.id}")]
            reply_markup = InlineKeyboardMarkup([keyboard])
            await update.message.reply_text(f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€", reply_markup=reply_markup)
        if context.user_data['contatore'] < len(spese)-1:
            reply_keyboard = [["Vedi le prossime 5 spese"]]
           
            await update.message.reply_text("Vuoi vedere le prossime 5 spese?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return STATO1        
    
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")    
                  
def main():
    
    
    
    # Sostituisci con il token che ti ha dato BotFather
    token = TOKEN_API

    ## Crea l'oggetto Application
    application = Application.builder().token(token).build()
    
    

    logger.info("Bot avviato")

    # Aggiungi il gestore per il comando /start
    application.add_handler(CommandHandler("start", crea_utente))
    
    edit_spesa_handler = ConversationHandler(
        entry_points=[CommandHandler('editspesa', edit_spesa)],
        states={STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_spesa), CallbackQueryHandler(button)],
                STATO2: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_spesa_state2)]},
        fallbacks=[CommandHandler('annulla', cancel)],
    )
    application.add_handler(edit_spesa_handler)
    
    delete_spesa_cc_handler = ConversationHandler(
        entry_points=[CommandHandler('deletespesacc', delete_spesa_cc)],
        states={STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_spesa_cc),CallbackQueryHandler(button)]},
        fallbacks=[CommandHandler('annulla', cancel)],)
    application.add_handler(delete_spesa_cc_handler)
    
    delete_entrata_handler = ConversationHandler(
        entry_points=[CommandHandler('deleteentrata', delete_entrata)],
        states={STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_entrata),CallbackQueryHandler(button)]},
        fallbacks=[CommandHandler('annulla', cancel)],
    )
    
    delete_spesa_handler = ConversationHandler(
        entry_points=[CommandHandler('deletespesa', delete_spesa)],
        states={STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_spesa),CallbackQueryHandler(button)]},
        fallbacks=[CommandHandler('annulla', cancel)],
    )
    getSpesa = ConversationHandler( 
        entry_points=[CommandHandler('getspese', get_spesa)],
            states=
                {STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_spesa_secondo_stato)],
                    STATO2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_spesa_terzo_stato)],
                    STATO3: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_spesa_quarto_stato)]
                                        },
                fallbacks=[CommandHandler('annulla', cancel)],
                )
    getEntrate = ConversationHandler( 
        entry_points=[CommandHandler('getentrate', get_entrate)],
            states=
                {STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_entrate_secondo_stato)],
                    STATO2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_entrate_terzo_stato)],
                    STATO3: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_entrate_quarto_stato)]
                                        },
                fallbacks=[CommandHandler('annulla', cancel)],
                )
    addSpesa = ConversationHandler( 
        entry_points=[CommandHandler('addspesa', add_spesa)],
            states=
                {STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_spesa_state2)],
                    STATO2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_spesa_state3)],
                                        },
                fallbacks=[CommandHandler('annulla', cancel)],
                )
    addEntrata = ConversationHandler( 
        entry_points=[CommandHandler('addentrata', add_entrata)],
            states=
                {STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_entrata_state2)],
                    STATO2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_entrata_state3)],
                                        },
                fallbacks=[CommandHandler('annulla', cancel)],
                )
    addSpesaCc = ConversationHandler( 
    entry_points=[CommandHandler('addspesacc', add_spesa_cc)],
        states=
            {STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_spesa_cc_state2)],
                STATO2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_spesa_cc_state3)],
                STATO3: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_spesa_cc_state4)],
                STATO4: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_spesa_cc_state5)]
                                    },
            fallbacks=[CommandHandler('annulla', cancel)],
            )
    setBudget = ConversationHandler(
        entry_points=[CommandHandler('setbudget', set_budget)],
        states=
            {STATO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_budget_state2)]
            },
        fallbacks=[CommandHandler('annulla', cancel)],
    )
    
    application.add_handler(CommandHandler("getbudget",get_budget))
    application.add_handler(setBudget)
    application.add_handler(getEntrate)
    application.add_handler(addSpesa)
    application.add_handler(getSpesa)
    application.add_handler(addEntrata)
    application.add_handler(addSpesaCc)
    application.add_handler(CommandHandler("getspesecc", get_spese_cc))
    application.add_handler(CommandHandler("getsaldo", get_saldo))
    application.add_handler(delete_spesa_handler)
    application.add_handler(delete_entrata_handler)
    # Avvia il bot
    application.run_polling()

if __name__ == '__main__':
    db.init_db() 
    migrations.main()
    main()
