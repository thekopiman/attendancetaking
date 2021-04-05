import logging
from telegram import parsemode
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
import random

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


class Attendance():
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        # self.start()
        try:
            # content is the vectors of message after the "/set" command
            self.content = context.args
            self.reminder_timings = self.date_time_extraction(self.content)
            for timing in self.reminder_timings:
                self.timing = timing
                self.set_timer(self.update, self.content, self.timing)
            update.message.reply_text("The timings have been updated!")

        except UnboundLocalError:
            update.message.reply_text(
                'Please key in this month attendance in this format\n' + sample_attendance_format)

    def date_time_extraction(self, CallbackcontextContent) -> list:
        '''
        Analyse and return the correct datetime values of the context.args values of /set
        '''
        content = CallbackcontextContent
        rawdates = CallbackcontextContent[0::4]
        returnvalues = []
        for date in rawdates:
            shift = content[content.index(date)+2]
            work = content[content.index(date)+3]
            if shift == '1':
                if work == '(early)':
                    time = '0700'
                elif work == '(late)':
                    time = '0745'
                elif work == '(ssu)':
                    time = '0845'
                else:
                    # Create a callback function to MAIN to create an ERROR function for the user and also to the server
                    pass
            elif shift == '2':
                if work == '(ssu)':
                    time = '2045'
                elif work == '(patrol)':
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

    def date_time_convert_to_db(self, DateTimeFormat):
        return datetime.strftime(DateTimeFormat, "%d/%m/%Y %H%M")

    def set_timer(self, update: Update, context: CallbackContext, timing) -> None:
        # print("Hello this is running")
        print("self.timing", self.timing)
        due = datetime.now() - self.timing
        due = random.randint(10, 30)
        chat_id = update.message.chat_id
        print(chat_id)
        self.context.job_queue.run_once(
            self.message, due, context=chat_id, name=str(self.timing))
        print(self.context.job_queue.get_jobs_by_name)

    def message(self, context: CallbackContext) -> None:
        job = context.job
        time = datetime.strftime(self.timing, "%H%M")
        dict_times = {"0700": "Shift 1 Early", "0745": "Shift 1 Late",
                      "0845": "Shift 1 SSU", "2045": "Shift 2 SSU", "2030": "Shift 2", '0830': "Training"}
        text = '''
        <b>Date: {date} | {work}</b>

        Remember to clock in:
        {link}
        '''.format(date=datetime.strftime(self.timing, "%d/%m/%Y %H%M"), work=dict_times[time], link=self.request_links(self.timing))
        context.bot.send_message(
            job.context, text=text, parse_mode=parsemode.ParseMode.HTML)
        return None

    def request_links(self, timing) -> str:
        '''
        Returns a string of the link
        '''
        with open("websites.txt", "r") as r:
            txt = r.readlines()
            for line in txt:
                tpl = line.strip().split(" ")
                time = tpl[0]
                link = tpl[1]
                if timing > datetime.strptime(time, "%m/%Y") and timing < (datetime.strptime(time, "%m/%Y")+relativedelta(months=+1)):
                    # print(link)
                    return link


class DBUpdate():
    def __init__(self, source="db.sqlite3"):
        '''
        This DB is used as a backup if the system happens to shut down and a restart is necessary. The programme will then read through the data here and continue with the reminders for each individual according to their ID.
        '''
        self.user = None
        pass


class WebsiteLink():
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        try:
            self.content = context.args
            self.write_websites(self.website_extraction())
            update.message.reply_text("The link has been updated!")

        except UnboundLocalError:
            update.message.reply_text(
                'Please key in this month website link in this format\n' +
                sample_website_format
            )

    def website_extraction(self) -> tuple:
        if len(self.content) == 1:
            return None
        elif len(self.content) == 3:
            return (self.content[0], self.content[-1])
        else:
            raise UnboundLocalError

    def write_websites(self, tpl):
        if tpl == None:
            pass
        else:
            with open("websites.txt", "a+") as w:
                w.write(f'{tpl[0]} {tpl[1]}\n')


class Jobs():
    def __init__(self):
        '''
        Not completed
        '''
        self.jobs_list = []
        self.hex_jobs = []

    def addjob(self, date_time):
        self.jobs_list.append(date_time)

    def removejob(self):
        pass


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
        dispatcher.add_handler(CommandHandler("link", WebsiteLink))
        dispatcher.add_handler(CommandHandler("set", Attendance))
        # dispatcher.add_handler(CommandHandler("set", set_timer))
        # dispatcher.add_handler(CommandHandler("unset", unset))

        # Start the Bot
        updater.start_polling()

        # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
        # SIGABRT. This should be used most of the time, since start_polling() is
        # non-blocking and will stop the bot gracefully.
        updater.idle()

    def start(self, update: Update, _: CallbackContext) -> None:
        '''Start messages'''
        update.message.reply_text(
            'Hi! Use this to clock in and out!\n' + "Take note that this bot will not be able to remind you for ES dates or Special events")
        update.message.reply_text(
            'First, Please key in this month attendance in this format\n' + sample_attendance_format)
        update.message.reply_text(
            'Second, Please key in this month attendance website (optional - Indicate NIL) using the /link command\n' + sample_website_format)

    def help(self, update: Update, _: CallbackContext) -> None:
        '''Help Page'''
        update.message.reply_text('''
        Hi! This is the help message. To start, type the /start command. You may refer to the lists for the rest of the commands availble.
        /start - Start Command
        /help - This message
        /queue - Check the queue for your attendance taking
        /reset - Remove all the queued reminders
        ''')

    def queue(self, update: Update, context: CallbackContext) -> None:
        try:
            print("JOB QUEUE:", context.job_queue.get_jobs_by_name())
            update.message.reply_text(
                context.job_queue.get_jobs_by_name())
        except Exception:
            update.message.reply_text("Did you type /queue correctly?")

    def reset(self, update: Update, _: CallbackContext) -> None:
        pass


if __name__ == '__main__':
    start1 = main(token="1616284866:AAGdL-P156n68oK3zssjybJEmxp3qezAZ4Q")
