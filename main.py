import datetime
import json
import math

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import excel
from excel import add_stipendio
import spese
TOKEN_API = '7101960618:AAFdwl7hm7LSO9cbNY40JG6h19bSgEW5eX8'

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

lista_utenti = {}
lista_wb_utenti = []
# Funzione che gestisce il comando /start
async def start(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) not in lista_utenti:
        id = str(update.message.from_user.id)
        user = update.message.from_user.username

        lista_utenti[id] = user
        wb = excel.Excel(user,id)
        lista_wb_utenti.append(wb)
        print(datetime.datetime.now(),': Aggiunto utente ', update.message.from_user.username)
        await update.message.reply_text(f"Creato utente {update.message.from_user.username} ")
# Funzione principale per avviare il bot



async def saldoMensileCurr(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            split = update.message.text.split()
            if split[1:] != []:
                if  is_valid_number(split[1]) == False or float(split[1]) < 1 or float(split[1]) > 12:
                    await update.message.reply_text("Hai inserito un valore di mese non valido")
                    return
                else:
                    saldo = math.trunc(excel.saldo_totale_mensile(str(update.message.date.year), int(split[1]),
                                                       wb.getWb()))
                    data = '8/' + str(int(split[1]) + 1)
            else:
                saldo = math.trunc(excel.saldo_totale_mensile(str(update.message.date.year), update.message.date.month,wb.getWb()))
                data = '8/' + str(update.message.date.month + 1)
            await update.message.reply_text(f"Il tuo saldo previsto per il {data} e': {saldo}")
            return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def spesee(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):

            split = update.message.text.split()
            if split[1:] != []:
                if  is_valid_number(split[1]) == False or int(split[1]) < 1 or int(split[1]) > 12:
                    await update.message.reply_text("Hai inserito un valore di mese non valido")
                    return
                else:
                    saldo = math.trunc(excel.get_spese_varie(str(update.message.date.year), int(split[1]),
                                                                  wb.getWb()))
                    await update.message.reply_text(f"In questo mese hai effettuato un totale di spese varie di: {saldo}")
                    return
            else:
                saldo = excel.get_spese_varie(str(update.message.date.year), update.message.date.month,wb.getWb())

                await update.message.reply_text(f"In questo mese hai effettuato un totale di spese varie di: {saldo}")
                return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def saldoSommaSpese(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            saldo = excel.get_somma_spese(str(update.message.date.year), update.message.date.month,wb.getWb())

            await update.message.reply_text(f"In questo mese hai speso in totale: {saldo}")
            return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def addebitoCc(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):

            split = update.message.text.split()
            if split[1:] != []:
                if  is_valid_number(split[1]) == False or int(split[1]) < 1 or int(split[1]) > 12:
                    await update.message.reply_text("Hai inserito un valore di mese non valido")
                    return
                else:
                    saldo = math.trunc(excel.get_somma_spese_cc(str(update.message.date.year), int(split[1]),
                                                             wb.getWb()))
                    data = '5/' + str(int(split[1]) + 1)
                    await update.message.reply_text(
                        f"Il prossimo {data} ti verranno addebitati {saldo} Euro per la carta di credito")
                    return

            saldo = excel.get_somma_spese_cc(str(update.message.date.year), update.message.date.month,wb.getWb())
            data = '5/' + str(update.message.date.month + 1)
            await update.message.reply_text(f"Il prossimo {data} ti verranno addebitati {saldo} Euro per la carta di credito")
            return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def entrate(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            split = update.message.text.split()
            if split[1:] != []:
                split[1] = split[1].replace(',','.')
                if  is_valid_number(split[1]) == False:
                    await update.message.reply_text("Hai inserito un valore non valido")
                    return
                elif update.message.date.day < 8:
                    excel.add_entrate(str(update.message.date.year), update.message.date.month - 1, float(split[1]),
                                      wb.getWb(), wb.getFile())
                    await update.message.reply_text(f"Hai aggiunto un entrata di: {float(split[1])}",
                                                    parse_mode=ParseMode.HTML)
                    saldo = excel.get_entrate_totali(str(update.message.date.year), update.message.date.month - 1,
                                                     wb.getWb())
                    await update.message.reply_text(f"Questo mese hai un entrata totale di: {saldo}")
                    return
                else:
                    excel.add_entrate(str(update.message.date.year), update.message.date.month ,float(split[1]), wb.getWb(), wb.getFile())
                    await update.message.reply_text(f"Hai aggiunto un entrata di: {float(split[1])}", parse_mode=ParseMode.HTML)
                    saldo = excel.get_entrate_totali(str(update.message.date.year), update.message.date.month,wb.getWb())
                    await update.message.reply_text(f"Questo mese hai un entrata totale di: {saldo}")
                    return
            else:
                await update.message.reply_text("Hai inserito un valore non valido")
                return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def addSpesaVaria(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            split = update.message.text.split()
            if split[1:] != []:
                if  is_valid_number(split[1]) == False:
                    await update.message.reply_text("Hai inserito un valore non valido")
                    return
                elif update.message.date.day < 8:
                    excel.add_spesa_varia(str(update.message.date.year), update.message.date.month - 1 ,float(split[1]), wb.getWb(), wb.getFile())
                    await update.message.reply_text(f"Hai aggiunto una spesa di: {float(split[1])}", parse_mode=ParseMode.HTML)
                    return
                else:
                    excel.add_spesa_varia(str(update.message.date.year), update.message.date.month, float(split[1]),
                                          wb.getWb(), wb.getFile())
                    await update.message.reply_text(f"Hai aggiunto una spesa di: {float(split[1])}",
                                                    parse_mode=ParseMode.HTML)
                    return
            else:
                await update.message.reply_text("Hai inserito un valore non valido")
                return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def addSpesaCc(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            split = update.message.text.split()
            if split[1:] != []:
                if is_valid_number(split[1]) == False:
                    await update.message.reply_text("Hai inserito un valore non valido")
                    return
                else:
                    excel.add_spesa_cc(str(update.message.date.year), update.message.date.month, float(split[1]),
                                          wb.getWb(), wb.getFile())
                    await update.message.reply_text(f"Hai aggiunto una spesa di: {float(split[1])} con la carta di credito",
                                                    parse_mode=ParseMode.HTML)
                    return
            else:
                await update.message.reply_text("Hai inserito un valore non valido")
                return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def help_command(update: Update, context: CallbackContext):
    help_text = "Ecco i comandi disponibili:\n\n"
    help_text += "\n".join(f"{cmd} - {desc}" for cmd, desc in COMMANDS.items())

    await update.message.reply_text(help_text)

async def report(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            month = update.message.date.month
            if  update.message.date.day < 8:
                month = update.message.date.month - 1
            await update.message.reply_text(f"Ecco il report per questo mese:")


            saldo = excel.get_somma_spese_cc(str(update.message.date.year), month, wb.getWb())
            await update.message.reply_text(f"Hai raggiunto una spesa di: {saldo} con la carta di credito",
                                            parse_mode=ParseMode.HTML)
            saldo = excel.get_somma_spese(str(update.message.date.year), month, wb.getWb())
            await update.message.reply_text(f"Hai raggiunto una spesa di: {saldo} con la carta di debito",
                                            parse_mode=ParseMode.HTML)
            saldo = math.trunc(excel.spesa_totale_mensile(str(update.message.date.year), month, wb.getWb()))
            await update.message.reply_text(f"Raggiungendo un totale di {saldo} Euro",
                                            parse_mode=ParseMode.HTML)
            saldo = math.trunc(excel.get_entrate_totali(str(update.message.date.year), month, wb.getWb()))
            await  update.message.reply_text(f"A fronte di un totale di entrate di {saldo} Euro")

            saldo = excel.saldo_totale_mensile(str(update.message.date.year), month - 1, wb.getWb())
            await update.message.reply_text(f"Considerato che l'8 del mese scorso avevi un saldo di {saldo} Euro")

            saldo = math.trunc(excel.saldo_totale_mensile(str(update.message.date.year), month, wb.getWb()))
            await update.message.reply_text(f"Avrai un saldo previsto di {saldo} Euro il prossimo 8 del mese",
                                            parse_mode=ParseMode.HTML)

async def send_excel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            await context.bot.send_document(chat_id=chat_id, document=open(wb.getFile(), "rb"))

async def add_stipendio(update: Update, context: CallbackContext):
    for wb in lista_wb_utenti:
        if wb.getId() == str(update.message.from_user.id):
            split = update.message.text.split()
            if split[1:] != []:
                split[1] = split[1].replace(',', '.')
                if is_valid_number(split[1]) == False:
                    await update.message.reply_text("Hai inserito un valore non valido")
                    return
                else:
                    excel.add_stipendio(str(update.message.date.year), update.message.date.month, float(split[1]), wb.getWb(),
                                      wb.getFile())
                    await update.message.reply_text(f"Hai aggiunto uno stipendio di: {float(split[1])}",
                                                    parse_mode=ParseMode.HTML)
                    saldo = excel.get_entrate_totali(str(update.message.date.year), update.message.date.month, wb.getWb())
                    await update.message.reply_text(f"Questo mese hai un entrata totale di: {saldo}")
                    return
            else:
                await update.message.reply_text("Hai inserito un valore non valido")
                return
    await update.message.reply_text("Problema nella lettura del file dell'utente")

async def start_json(update: Update, context: CallbackContext):
    try:
        with open('Registri/registri.json', 'r') as f:
            lista_utenti = json.load(f)
            for x in lista_utenti:
                if x == update.message.from_user.username:
                    await update.message.reply_text(f"Utente {update.message.from_user.username} gia esistente")
                    return
            reg = {}
            lista_utenti[update.message.from_user.username] = {
                'Spese' : [], 'Entrate' : []
            }

            try:
                 with open('Registri/registri.json', 'w') as f:
                    json.dump(lista_utenti, f)
                    await update.message.reply_text(f"Utente {update.message.from_user.username} inserito")
            except Exception as e:
                print(f"{datetime.datetime.now()}: {e}")
                await update.message.reply_text(f"Errore nella creazione, riprovare")
    except Exception as e2:
        print(f"{datetime.datetime.now()}: {e2}")
        await update.message.reply_text("Errore nella creazione")

async def add_spesa(update: Update, context: CallbackContext):
    try:
        with open('Registri/registri.json', 'r') as f:
            lista_utenti = json.load(f)
            for utente, liste in lista_utenti.items():
                if utente == update.message.from_user.username:
                    split = update.message.text.split()
                    try:
                        spesa = float(split[1])
                    except IndexError:
                        spesa = 0
                    except:
                        await update.message.reply_text("Hai inserito un valore non valido")
                        return
                    finally:
                        try:
                            descrizione = split[2]
                            out = spese.add_spesa(liste["Spese"], spesa, descrizione)
                        except IndexError:
                            out = spese.add_spesa(liste["Spese"], spesa)
                break
        with open('Registri/registri.json', 'w') as f:
            json.dump(lista_utenti, f)
            await update.message.reply_text(f"Inserito:\n{out}")
    except Exception as e2:
        print(f"{datetime.datetime.now()}: {e2}")
        await update.message.reply_text("Errore interno ")

async def get_spesa(update: Update, context: CallbackContext):
    split = update.message.text.split()
    string_out = ''
    out = []
    try:
        inizio = split[1]
        try:
            fine = split[2]
            with open('Registri/registri.json', 'r') as f:
                lista_utenti = json.load(f)
                for utente, liste in lista_utenti.items():
                    if utente == update.message.from_user.username:
                       out = spese.get_spesa_intervallo(liste["Spese"],inizio,fine)
        except IndexError:
            with open('Registri/registri.json', 'r') as f:
                lista_utenti = json.load(f)
                for utente, liste in lista_utenti.items():
                    if utente == update.message.from_user.username:
                      out = spese.get_spesa_intervallo(liste["Spese"],inizio)
    except IndexError:
        with open('Registri/registri.json', 'r') as f:
            lista_utenti = json.load(f)
            for utente, liste in lista_utenti.items():
                if utente == update.message.from_user.username:
                   out = spese.get_spesa_mensile(liste["Spese"])

    finally:
        if len(out) > 0:
            for spesa in out:
                string_out += f"{spesa}\n"
            await update.message.reply_text(string_out)
        else:
            await update.message.reply_text("Non ci sono spese per il mese corrente")





def is_valid_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def main():
    # Sostituisci con il token che ti ha dato BotFather
    token = TOKEN_API

    ## Crea l'oggetto Application
    application = Application.builder().token(token).build()

    # Aggiungi il gestore per il comando /start
    application.add_handler(CommandHandler("start", start_json))
    application.add_handler(CommandHandler("addSpesa", add_spesa))
    application.add_handler(CommandHandler("getSpese", get_spesa))
    """    
    application.add_handler(CommandHandler("saldo", saldoMensileCurr))
    application.add_handler(CommandHandler("speseVarie", spese))
    application.add_handler(CommandHandler("addebitoCc", addebitoCc))
    application.add_handler(CommandHandler("sommaSpese", saldoSommaSpese))
    application.add_handler(CommandHandler("add", entrate))
    application.add_handler(CommandHandler("addSpesa", addSpesaVaria))
    application.add_handler(CommandHandler("addSpesaCc", addSpesaCc))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", send_excel))
    application.add_handler(CommandHandler("addStipendio", add_stipendio))"""
    # Avvia il bot
    application.run_polling()

if __name__ == '__main__':
    main()
