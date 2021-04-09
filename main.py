import logging
from telegram import parsemode
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
import random
import os
from DBUpdate import DBUpdate

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

sample_attendance_format = '''
Format:
dd/mm/yyyy - 1 (early/ssu)
dd/mm/yyyy - 1 (late/ssu)
dd/mm/yyyy - 2 (ssu/patrol)
dd/mm/yyyy - Training

Example:
/set
07/03/2021 - 1 (ssu)
08/03/2021 - 1 (late)
11/03/2021 - 2 (ssu)
12/03/2021 - 2 (patrol)
15/03/2021 - 1 (early)
16/03/2021 - 1 (early)
19/03/2021 - 1 (early)
20/03/2021 - 1 (early)
23/03/2021 - Training (nil)
'''

sample_website_format = '''
Example:
/link
mm/yyyy - https://form.gov.sg/Xxxx
'''

sample_timing_format = '''
Examples:
Date: dd/mm/yyyy
Clock in: HHMM
Clock out: HHMM

Date: dd/mm/yyyy
Clock in: HHMM

Date: dd/mm/yyyy
Clock out: HHMM
'''


class Attendance():
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        # self.start()
        try:
            # content is the vectors of message after the "/set" command
            self.content = context.args
            if self.content == []:
                raise UnboundLocalError

            # Clock In
            self.reminder_timings_clock_in = self.date_time_extraction_clock_in(
                self.content)
            for timing in self.reminder_timings_clock_in:
                self.timing = timing
                self.set_timer_clock_in(self.update, self.content, self.timing)

            # Clock Out
            self.reminder_timings_clock_out = self.date_time_extraction_clock_out(
                self.content)
            for timing in self.reminder_timings_clock_out:
                self.timing = timing
                self.set_timer_clock_out(
                    self.update, self.content, self.timing)

            # print("HELLLLLLLOOOOOOOO       ", update.message.from_user)
            update.message.reply_text("The timings have been updated!")

        except UnboundLocalError:
            update.message.reply_text(
                'Please key in this month attendance in this format\n' + sample_attendance_format)

    def date_time_extraction_clock_in(self, CallbackcontextContent) -> list:
        '''
        Analyse and return the correct datetime values of the context.args values of /set
        '''
        content = CallbackcontextContent
        rawdates = CallbackcontextContent[0::4]
        returnvalues = []
        for date in rawdates:
            shift = content[content.index(date)+2]
            work = content[content.index(date)+3][1:-1].lower()
            if shift == '1':
                if work == 'early':
                    time = '0700'
                elif work == 'late':
                    time = '0745'
                elif work == 'ssu':
                    time = '0845'
                else:
                    # Create a callback function to MAIN to create an ERROR function for the user and also to the server
                    pass
            elif shift == '2':
                if work == 'ssu':
                    time = '2045'
                elif work == 'patrol':
                    time = '2030'
                else:
                    # Create a callback function to MAIN to create an ERROR function for the user and also to the server
                    pass
            elif shift == 'Training':
                time = '0830'
            else:
                # Create a callback function to MAIN to create an ERROR function for the user and also to the server
                pass
            returnvalues.append(datetime.strptime(
                date + " " + time, "%d/%m/%Y %H%M"))

        return returnvalues

    def date_time_extraction_clock_out(self, CallbackcontextContent) -> list:
        '''
        Analyse and return the correct datetime values of the context.args values of /set
        '''
        content = CallbackcontextContent
        rawdates = CallbackcontextContent[0::4]
        returnvalues = []
        night = False
        for date in rawdates:
            shift = content[content.index(date)+2]
            work = content[content.index(date)+3][1:-1].lower()
            if shift == '1':
                if work == 'early':
                    time = '2045'
                elif work == 'late':
                    time = '2115'
                elif work == 'ssu':
                    time = '1000'
                else:
                    # Create a callback function to MAIN to create an ERROR function for the user and also to the server
                    pass
            elif shift == '2':
                night = True
                if work == 'ssu':
                    time = '1000'
                elif work == 'patrol':
                    time = '0945'
                else:
                    # Create a callback function to MAIN to create an ERROR function for the user and also to the server
                    pass
            elif shift == 'Training':
                time = '1500'
            else:
                # Create a callback function to MAIN to create an ERROR function for the user and also to the server
                pass

            if night:
                returnvalues.append(datetime.strptime(
                    date + " " + time, "%d/%m/%Y %H%M") + relativedelta(days=+1))
            else:
                returnvalues.append(datetime.strptime(
                    date + " " + time, "%d/%m/%Y %H%M"))

        return returnvalues

    def set_timer_clock_in(self, update: Update, context: CallbackContext, timing) -> None:
        # print("Hello this is running")
        due = datetime.now() - self.timing
        #
        # Remember to delete this line of code after testing is done.
        #
        # due = random.randint(10, 30)
        due = datetime.now() - (datetime.now() - relativedelta(seconds=random.randint(5, 10)))

        chat_id = update.message.chat_id
        # print(chat_id)
        self.context.job_queue.run_once(
            self.message_in, due, context=chat_id, name=str(self.timing) + " | Clock In")
        # print("Hello good afternoon:   ",
        #       self.context.job_queue.get_jobs_by_name(str(self.timing))[0].name)

    def set_timer_clock_out(self, update: Update, context: CallbackContext, timing) -> None:
        # print("Hello this is running")
        due = datetime.now() - self.timing
        #
        # Remember to delete this line of code after testing is done.
        #
        # due = random.randint(10, 30)
        due = datetime.now() - (datetime.now() - relativedelta(seconds=random.randint(15, 20)))

        chat_id = update.message.chat_id
        # print(chat_id)
        self.context.job_queue.run_once(
            self.message_out, due, context=chat_id, name=str(self.timing) + " | Clock Out")
        # print("Hello good afternoon:   ",
        #       self.context.job_queue.get_jobs_by_name(str(self.timing))[0].name)

    def message_in(self, context: CallbackContext) -> None:
        job = context.job
        timing = datetime.now()
        dict_times = {"0700": "Shift 1 Early", "0745": "Shift 1 Late",
                      "0845": "Shift 1 SSU", "2045": "Shift 2 SSU", "2030": "Shift 2", '0830': "Training"}

        try:
            text = '''
            <b>Date: {date} | {work}</b>\nRemember to clock in:\n{link}
            '''.format(date=datetime.strftime(timing, "%d/%m/%Y %H%M"), work=dict_times[datetime.strftime(timing, "%H%M")], link=DBUpdate.request_links(timing, self.update.message.from_user['id']))  # Indicate User_id in the future for the last of the parameter
        except KeyError:
            text = '''
            <b>Date: {date}</b>\nRemember to clock in:\n{link}
            '''.format(date=datetime.strftime(timing, "%d/%m/%Y %H%M"), link=DBUpdate.request_links(timing, self.update.message.from_user['id']))  # Indicate User_id in the future for the last of the parameter
        finally:
            clock_in = '''/timing\nDate: {date}\nClock in: HHMM
            '''.format(date=datetime.strftime(timing, "%d/%m/%Y"))
            context.bot.send_message(
                job.context, text=text, parse_mode=parsemode.ParseMode.HTML)

            context.bot.send_message(
                job.context, text=clock_in, parse_mode=parsemode.ParseMode.HTML)

        return None

    def message_out(self, context: CallbackContext) -> None:
        job = context.job
        timing = datetime.now()
        dict_times = {"2045": "Shift 1 Early", "2115": "Shift 1 Late",
                      "2200": "Shift 1 SSU", "1000": "Shift 2 SSU", "0945": "Shift 2", '1500': "Training"}

        try:
            text = '''
            <b>Date: {date} | {work}</b>\nRemember to clock out:\n{link}
            '''.format(date=datetime.strftime(timing, "%d/%m/%Y %H%M"), work=dict_times[datetime.strftime(timing, "%H%M")], link=DBUpdate.request_links(timing, self.update.message.from_user['id']))  # Indicate User_id in the future for the last of the parameter
        except KeyError:
            text = '''
            <b>Date: {date}</b>\nRemember to clock out:\n{link}'''.format(date=datetime.strftime(timing, "%d/%m/%Y %H%M"), link=DBUpdate.request_links(timing, self.update.message.from_user['id']))  # Indicate User_id in the future for the last of the parameter
        finally:
            clock_out = '''/timing\nDate: {date}\nClock Out: HHMM'''.format(
                date=datetime.strftime(timing, "%d/%m/%Y"))
            context.bot.send_message(
                job.context, text=text, parse_mode=parsemode.ParseMode.HTML)
            context.bot.send_message(
                job.context, text=clock_out, parse_mode=parsemode.ParseMode.HTML)
        return None


class main():
    def __init__(self, token):
        # Create the Updater and pass it your bot's token.
        updater = Updater(token)
        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # on different commands - answer in Telegram
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help))
        dispatcher.add_handler(CommandHandler("queue", self.queue))
        dispatcher.add_handler(CommandHandler("reset", self.reset))
        dispatcher.add_handler(CommandHandler("link", DBUpdate.update_website))
        dispatcher.add_handler(CommandHandler("set", Attendance))
        dispatcher.add_handler(CommandHandler("timing", DBUpdate))
        dispatcher.add_handler(CommandHandler(
            "gettiming", DBUpdate.get_timing))

        # Start the Bot
        updater.start_polling()

        # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
        # SIGABRT. This should be used most of the time, since start_polling() is
        # non-blocking and will stop the bot gracefully.
        updater.idle()

    def start(self, update: Update, _: CallbackContext) -> None:
        '''Start messages'''
        update.message.reply_text(
            'Hi! Use this to clock in and out!\n' + "Take note that this bot will not be able to remind you for ES dates or Special events (Watch out for Future Updates!!)")
        update.message.reply_text(
            'First, Please key in this month attendance in this format\n' + sample_attendance_format)
        update.message.reply_text(
            'Second, Please key in this month attendance website (optional) using the /link command\n' + sample_website_format)

    def help(self, update: Update, _: CallbackContext) -> None:
        '''Help Page'''
        update.message.reply_text('''
        Hi! This is the help message. To start, type the /start command. You may refer to the lists for the rest of the commands availble.
        /start - Start Command
        /help - This message
        /queue - Check the queue for your attendance taking
        /reset - Remove all the queued reminders
        /link - To create a new link for the next month MA. Type /link for the format.
        /set - To create reminders according to the date and details mentioned. Type /set for the format.
        /timing - Used for Clocking in and out. Type /timing for the format.
        ''')

    def queue(self, update: Update, context: CallbackContext) -> None:
        try:
            # lists_of_jobs = ["2021-03-08 07:45:00", "2021-03-07 08:45:00", "2021-03-08 21:15:00", "2021-03-07 10:00:00"]
            list_of_jobs = [x.name for x in context.job_queue.jobs()]
            message_template = '''<b>Current Queue: </b>\n'''
            if len(list_of_jobs) >= 1:
                for i in range(len(list_of_jobs)):
                    message_template = f'{message_template}{i+1}. {list_of_jobs[i]}\n'
            else:
                message_template = '<b>There are no reminders queued!</b>'

            update.message.reply_text(
                message_template, parse_mode=parsemode.ParseMode.HTML)
        except Exception:
            update.message.reply_text("Did you type /queue correctly?")

    def reset(self, update: Update, context: CallbackContext) -> None:
        try:
            list_of_jobs = context.job_queue.jobs()
            for job in list_of_jobs:
                job.schedule_removal()
            update.message.reply_text(
                "All of the reminders have been deleted!")

        except Exception:
            update.message.reply_text("Did you type /reset correctly?")


if __name__ == '__main__':
    # The Telegram Token is in the Environment Variable in the system.
    # You may uncomment the following code if you would like to parse the token directly inside (Not recommanded due to security issues)
    #start1 = main(token="XXXX-XXXXXXTokenXXXX")

    start1 = main(token=os.getenv("TELEGRAM_TOKEN_ATTENDANCE"))
