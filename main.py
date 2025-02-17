from datetime import datetime, timedelta
import json
import math

from telegram import ReplyKeyboardMarkup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, filters, MessageHandler, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler

import entrate
import errors
import excel
from entrate import Entrate
from excel import add_stipendio
import spese
from spese import Spesa
import db
TOKEN_API = '7101960618:AAFdwl7hm7LSO9cbNY40JG6h19bSgEW5eX8'
user_data = {}
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

STATO1,STATO2,STATO3,STATO4 = range(4)

async def crea_utente(update: Update, context: CallbackContext):
    utente = update.message.from_user.username
    try:
        db.create(utente)
    except errors.DescriptionError as e:
        await update.message.reply_text(f"{e}")
    await update.message.reply_text(f"Utente {utente} creato")

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
            fine = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            inizio = (datetime.now() - timedelta(days=30)).strftime("%Y/%m/%d %H:%M:%S")
            spese = db.get_spesa(utente, fine,inizio)
            if spese == []:
                await update.message.reply_text("Nessuna spesa trovata")
                return ConversationHandler.END
            for spesa in spese:
                out += f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€\n"
            await update.message.reply_text(f"Spese:\n {out}")
        
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")

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

async def get_spesa_quarto_stato(update: Update, context: CallbackContext):
    try:
        if update.message.text == 'x':
            data = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
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
        spese = db.get_spesa(utente, context.user_data['fine'], context.user_data['inizio'])
        if spese == []:
            await update.message.reply_text("Nessuna spesa trovata")
            return ConversationHandler.END
        for spesa in spese:
            out += f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€\n"
        await update.message.reply_text(f"Spese:\n {out}")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")

async def add_spesa(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Inserisci la descrizione della spesa")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
async def add_spesa_state2(update: Update, context: CallbackContext):
    try:
        context.user_data['descrizione'] = update.message.text
        await update.message.reply_text("Inserisci l'importo della spesa")
        return STATO2
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}") 
async def add_spesa_state3(update: Update, context: CallbackContext):
    try:
        ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        context.user_data['importo'] = update.message.text
        db.salva_spesa(update.message.from_user.username, context.user_data['descrizione'], context.user_data['importo'], ts)
        await update.message.reply_text("Spesa salvata")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")

async def add_entrata(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Inserisci la descrizione dell'entrata")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        
async def add_entrata_state2(update: Update, context: CallbackContext):
    try:
        context.user_data['descrizione'] = update.message.text
        await update.message.reply_text("Inserisci l'importo dell'entrata")
        return STATO2
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
async def add_entrata_state3(update: Update, context: CallbackContext):
    try:
        ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        context.user_data['importo'] = update.message.text
        db.salva_entrata(update.message.from_user.username, context.user_data['descrizione'], context.user_data['importo'], ts)
        await update.message.reply_text("Entrata salvata")
        return ConversationHandler.END
    except Exception as e: 
        await update.message.reply_text(f"Errore, riprova \n{e}")

async def get_entrate(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Vuoi ricercare per un intervallo oppure per gli ultimi 30 giorni?")
        reply_keyboard = [['Intervallo', 'Mensile']]
        await update.message.reply_text("Scegli un'opzione", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
async def get_entrate_secondo_stato(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        reply = update.message.text
        if reply == "Intervallo":
            await update.message.reply_text("Inserisci la data di inizio (gg/mm/aaaa)")
            return STATO2
        else:
            out = ''
            fine = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            inizio = (datetime.now() - timedelta(days=30)).strftime("%Y/%m/%d %H:%M:%S")
            entrate = db.get_entrata(utente, fine,inizio)
            if entrate == []:
                await update.message.reply_text("Nessuna entrata trovata")
                return ConversationHandler.END
            for entrata in entrate:
                out += f"{entrata.descrizione} | {entrata.timestamp} | Importo: {entrata.importo}€\n"
            await update.message.reply_text(f"Entrate:\n {out}")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
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
async def get_entrate_quarto_stato(update: Update, context: CallbackContext):
    try:
        if update.message.text == 'x':
            data = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
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
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}") 
 
    
async def cancel(update: Update, context):
    """Interrompe la conversazione."""
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END

async def debug(update: Update, context: CallbackContext):
    await update.message.reply_text(f"{context.user_data}")

async def get_saldo(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        saldo = db.get_saldo(utente)
        await update.message.reply_text(f"Saldo il prossimo 8 del mese: {saldo} Euro")
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
        
async def add_spesa_cc(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Inserisci la descrizione della spesa")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
async def add_spesa_cc_state2(update: Update, context: CallbackContext):
    try:
        context.user_data['descrizione'] = update.message.text
        await update.message.reply_text("Inserisci l'importo della spesa")
        return STATO2
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
async def add_spesa_cc_state3(update: Update, context: CallbackContext):
    try:
        ts = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        context.user_data['importo'] = update.message.text
        await update.message.reply_text("Hai effettuato un pagamento a rate?")
        reply_keyboard = [['Si', 'No']]
        await update.message.reply_text("Scegli un'opzione", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return STATO3
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        
async def add_spesa_cc_state4(update: Update, context: CallbackContext):
    try:
        if update.message.text == 'Si':
            await update.message.reply_text("Inserisci il numero di rate")
            return STATO4
        else:
            db.add_spesa_cc(update.message.from_user.username, float(context.user_data['importo']), context.user_data['descrizione'], datetime.now().strftime("%Y/%m/%d %H:%M:%S"), 1)
            await update.message.reply_text("Spesa salvata")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")    
 
async def add_spesa_cc_state5(update: Update, context: CallbackContext):
    try:
        rate = int(update.message.text)
        if rate > 13 or rate < 1:
            await update.message.reply_text("Numero di rate non valido, riprova")
            return STATO4
        db.add_spesa_cc(update.message.from_user.username, float(context.user_data['importo']), context.user_data['descrizione'],  datetime.now().strftime("%Y/%m/%d %H:%M:%S"), rate)
        await update.message.reply_text("Spesa salvata")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")   
    

async def get_spese_cc(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        spese = db.get_spese_cc(utente)
        out = ''
        for spesa in spese:
            out += f"{spesa.descrizione} | {spesa.timestamp} | Importo: {spesa.importo}€ | Mensilita: {spesa.mensilita} | Rata: {round(spesa.importo/spesa.mensilita,2)}\n"
        await update.message.reply_text(f"Spese:\n {out}")
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")


async def set_budget(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("Inserisci il budget mensile")
        return STATO1
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")
        
async def set_budget_state2(update: Update, context: CallbackContext):
    try:
        budget = update.message.text
        db.set_budget(update.message.from_user.username, budget)
        await update.message.reply_text("Budget salvato")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova \n{e}")

async def get_budget(update: Update, context: CallbackContext):
    try:
        utente = update.message.from_user.username
        budget = db.get_budget(utente)
        await update.message.reply_text(f"Budget mensile: {budget} Euro")
        
        #calcolo budget mensile
        if update.message.date.day < 8:
            if update.message.date.month == 1:
                inizio = datetime(update.message.date.year-1, 12, 8,0,0,0)
                fine =datetime(update.message.date.year, 1, 8,0,0,0)
            else:
                inizio = datetime(update.message.date.year, update.message.date.month-1, 8,0,0,0)
                fine = datetime(update.message.date.year, update.message.date.month, 8,0,0,0)
        else:
            if update.message.date.month == 12:
                inizio = datetime(update.message.date.year,12,8,0,0,0)
                fine = datetime(update.message.date.year+1, 1, 8,0,0,0)
            else:
                inizio = datetime(update.message.date.year, update.message.date.month, 8,0,0,0)
                fine = datetime(update.message.date.year, update.message.date.month+1, 8,0,0,0)
        spese_mensili = db.get_spesa(utente, fine, inizio)
        totale = spese_mensili[-1]
        if totale.importo > budget:
            await update.message.reply_text(f"ATTENZIONE! Hai superato il budget mensile di {totale.importo - budget} Euro")
        else:
            await update.message.reply_text(f"A fronte di una spesa di {totale} Euro, questo mese puoi spendere ancora {budget-totale.importo} Euro")
        
        #calcolo budget settimanale
        inizio_oggi = datetime(update.message.date.year, update.message.date.month, update.message.date.day,0,0,0)
        weekday = update.message.date.weekday()
        delta_fine = 7-weekday
        inizio_settimana = inizio_oggi - timedelta(days=weekday)
        fine_settimana = inizio_oggi + timedelta(days=delta_fine)
        spesa_settimanale = db.get_spesa(utente, fine_settimana, inizio_settimana)
        budget_settimanale = budget/4
        if spesa_settimanale[-1].importo > budget_settimanale:
            await update.message.reply_text(f"ATTENZIONE! Hai superato il budget settimanale di {spesa_settimanale[-1].importo - budget_settimanale} Euro")
        else:
            await update.message.reply_text(f"A fronte di una spesa di {spesa_settimanale[-1].importo} Euro, questa settimana puoi spendere ancora {budget_settimanale-spesa_settimanale[-1].importo} Euro")
        

        
        #calcolo budget giornaliero
        domani = inizio_oggi + timedelta(days=1)
        spesa_giornaliera = db.get_spesa(utente, domani, inizio_oggi)
        budget_giornaliero = budget/(fine-inizio).days
        if spesa_giornaliera[-1].importo > budget_giornaliero:
            await update.message.reply_text(f"ATTENZIONE! Hai superato il budget giornaliero di {spesa_giornaliera[-1].importo - budget_giornaliero} Euro")
        else:
            await update.message.reply_text(f"A fronte di una spesa di {spesa_giornaliera[-1].importo} Euro, oggi puoi spendere ancora {budget_giornaliero-spesa_giornaliera[-1].importo} Euro")
            
        
        
        
        
    except Exception as e:
        await update.message.reply_text(f"Errore, riprova {e}")
    
def main():
    # Sostituisci con il token che ti ha dato BotFather
    token = TOKEN_API

    ## Crea l'oggetto Application
    application = Application.builder().token(token).build()
    
    

    

    # Aggiungi il gestore per il comando /start
    application.add_handler(CommandHandler("start", crea_utente))
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
    
    application.add_handler(setBudget)
    application.add_handler(getEntrate)
    application.add_handler(addSpesa)
    application.add_handler(getSpesa)
    application.add_handler(addEntrata)
    application.add_handler(addSpesaCc)
    application.add_handler(CommandHandler("getsaldo", get_saldo))

    # Avvia il bot
    application.run_polling()

if __name__ == '__main__':
    db.init_db()
    main()
