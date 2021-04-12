import logging
import os
from telegram import parsemode
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
import sqlite3

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

sample_website_format = '''
Example:
/link
mm/yyyy - https://form.gov.sg/Xxxx
'''


class DBUpdate():
    def __init__(self, update: Update, context: CallbackContext):
        '''
        This DB is used as a backup if the system happens to shut down and a restart is necessary. The programme will then read through the data here and continue with the reminders for each individual according to their ID.
        This module is also used to update the website link for the user.
        '''
        self.directory = os.path.dirname(
            os.path.realpath(__file__)) + "\Database\\"
        self.update = update
        self.context = context
        self.content = context.args
        try:
            if self.content != []:
                self.timing(self.update, self.context)
            else:
                raise UnboundLocalError
        except UnboundLocalError:
            update.message.reply_text(
                "Please key in today's attendance in this format\n\n" + '/timing\nDate: dd/mm/yyyy\nClock in/out: HHMM')

    @classmethod
    def request_links(self, timing, user_id: int, directory=os.path.dirname(
            os.path.realpath(__file__)) + "\Database\\") -> str:
        '''
        Returns a string of the link
        '''
        return_link = "NIL"
        # print(f'{directory}{str(user_id)}.sqlite')
        if os.path.isfile(f'{directory}{str(user_id)}.sqlite'):
            conn = sqlite3.connect(f'{directory}{str(user_id)}.sqlite')
            cur = conn.cursor()
        else:
            conn = sqlite3.connect(f'{directory}{str(user_id)}.sqlite')
            cur = conn.cursor()
            cur.execute('CREATE TABLE website_link(date TEXT, website TEXT)')
            cur.execute(
                'CREATE TABLE clocking(date TEXT, clock_in INTEGER, clock_out INTEGER)')

        cur.execute('SELECT * from website_link')
        for aline in cur.fetchall():
            time = aline[0]
            link = aline[1]
            if timing > datetime.strptime(time, "%m/%Y") and timing < (datetime.strptime(time, "%m/%Y")+relativedelta(months=+1)):
                # print(link)
                return_link = link

        return return_link

    def timing(self, update: Update, context: CallbackContext):
        clock_in, clock_out = self.timecheck(
            "in", context.args), self.timecheck("out", context.args)
        if clock_in == None and clock_out == None:
            raise UnboundLocalError
        user_id = update.message.from_user['id']
        # print(f'{self.directory}{str(user_id)}.sqlite')
        if os.path.isfile(f'{self.directory}{str(user_id)}.sqlite'):
            conn = sqlite3.connect(f'{self.directory}{str(user_id)}.sqlite')
            cur = conn.cursor()
        else:
            conn = sqlite3.connect(f'{self.directory}{str(user_id)}.sqlite')
            cur = conn.cursor()
            cur.execute('CREATE TABLE website_link(date TEXT, website TEXT)')
            cur.execute(
                'CREATE TABLE clocking(date TEXT, clock_in INTEGER, clock_out INTEGER)')

        cur.execute('SELECT date from clocking')
        # print(cur.fetchall())
        date_present = False
        msg_date = self.datecheck(context.args)
        if msg_date != False:
            # Checks if the date given in the the msg is present in the Database
            list_of_dates = cur.fetchall()
            for i in [x[0] for x in list_of_dates]:
                if msg_date == i:
                    if clock_in != None:
                        cur.execute(
                            'UPDATE clocking set clock_in = ? where date = ?', (clock_in, i))
                    if clock_out != None:
                        cur.execute(
                            'UPDATE clocking set clock_out = ? where date = ?',  (clock_out, i))
                    date_present = True
        else:
            raise ValueError

        if date_present == False:
            if clock_in != None and clock_out != None:
                cur.execute(
                    'INSERT INTO clocking(date,clock_in, clock_out) VALUES (?,?,?)', (msg_date, clock_in, clock_out))
            elif clock_in != None and clock_out == None:
                cur.execute(
                    'INSERT INTO clocking(date,clock_in) VALUES (?,?)', (msg_date, clock_in, ))
            elif clock_in == None and clock_out != None:
                cur.execute(
                    'INSERT INTO clocking(date,clock_out) VALUES (?,?)', (msg_date, clock_out, ))
        cur.execute('SELECT * from clocking')

        conn.commit()
        update.message.reply_text("The timing has been updated!")

    @classmethod
    def timecheck(self, in_out, content):
        '''
        Returns the Clock in or Out from the content. Else return None
        '''
        content = [x.lower() for x in content]
        if in_out in content or str(in_out+":") in content:
            try:
                index = content.index(in_out)
            except ValueError:
                index = content.index(str(in_out + ":"))
            time = 'xxxx'
            for i in content[index:]:
                try:
                    time = int(i)
                    break
                except ValueError:
                    pass

            if type(time) != int:
                return None
            else:
                return time

    @classmethod
    def datecheck(self, content):
        '''
        Return the date from the content. Else Return False
        '''
        content = [x.lower() for x in content]
        if 'date' in content or 'date:' in content:
            try:
                index = content.index('date')
            except:
                index = content.index('date:')
            date = 'xxxxxxxx'
            for i in content[index:]:
                try:
                    date = datetime.strptime(i, "%d/%m/%Y")
                    break
                except ValueError:
                    pass
            if date == 'xxxxxxxx':
                return False
            else:
                return str(datetime.strftime(date, "%d/%m/%Y"))

    @classmethod
    def update_website(self, update: Update, context: CallbackContext):
        try:
            content = context.args
            DBUpdate.write_websites(tpl=DBUpdate.website_extraction(
                content), user_id=update.message.from_user['id'])
            update.message.reply_text("The link has been updated!")
        except UnboundLocalError:
            update.message.reply_text(
                'Please key in this month website link in this format\n' +
                sample_website_format
            )

    @classmethod
    def write_websites(self, tpl: tuple, user_id: int, directory=os.path.dirname(os.path.realpath(__file__)) + "\DataBase\\") -> str:
        if tpl == None:
            pass
        else:
            if os.path.isfile(f'{directory}{str(user_id)}.sqlite'):
                conn = sqlite3.connect(f'{directory}{str(user_id)}.sqlite')
                cur = conn.cursor()
            else:
                conn = sqlite3.connect(f'{directory}{str(user_id)}.sqlite')
                cur = conn.cursor()
                cur.execute(
                    'CREATE TABLE website_link(date TEXT, website TEXT)')
                cur.execute(
                    'CREATE TABLE clocking(date TEXT, clock_in INTEGER, clock_out INTEGER)')

            cur.execute('SELECT date from website_link')
            list_of_dates = [x[0] for x in cur.fetchall()]
            if tpl[0] in list_of_dates:
                cur.execute(
                    'UPDATE website_link SET website = ? where date = ?', (tpl[1], tpl[0]))
            else:
                cur.execute(
                    'INSERT INTO website_link(date, website) VALUES (?,?)', (tpl[0], tpl[1]))
        conn.commit()

    @classmethod
    def website_extraction(self, content) -> tuple:
        if len(content) == 1:
            return None
        elif len(content) == 3:
            return (content[0], content[-1])
        else:
            raise UnboundLocalError

    @classmethod
    def get_timing(self, update: Update, context: CallbackContext):
        '''
        Send a message to the user regarding the MA timing for the month
        '''
        try:
            requested_month = datetime.strptime(context.args[0], "%m/%Y")
            directory = os.path.dirname(
                os.path.realpath(__file__)) + "\Database\\"
            user_id = update.message.from_user['id']
            if os.path.isfile(f'{directory}{str(user_id)}.sqlite'):
                conn = sqlite3.connect(f'{directory}{str(user_id)}.sqlite')
                cur = conn.cursor()
            else:
                conn = sqlite3.connect(f'{directory}{str(user_id)}.sqlite')
                cur = conn.cursor()
                cur.execute(
                    'CREATE TABLE website_link(date TEXT, website TEXT)')
                cur.execute(
                    'CREATE TABLE clocking(date TEXT, clock_in INTEGER, clock_outINTEGER)')
            cur.execute('Select * from clocking')
            data = cur.fetchall()
            return_data = []
            for row in data:
                date = row[0]
                clock_in = row[1]
                clock_out = row[2]
                if datetime.strptime(date, "%d/%m/%Y") > requested_month and datetime.strptime(date, "%d/%m/%Y") < requested_month+relativedelta(months=+1):
                    return_data.append((date, clock_in, clock_out))
            message_template = f'<b>{context.args[0]} MA Timings</b>\nDate   |  Clock In  | Clock Out\n'
            for date, clock_in, clock_out in return_data:
                message_template += f'{date} | {clock_in} | {clock_out}\n'
            update.message.reply_text(
                message_template, parse_mode=parsemode.ParseMode.HTML)
        except (UnboundLocalError, IndexError, ValueError):
            update.message.reply_text(
                "Please key in month's MA timing in this format\n/gettiming mm/yyyy")

    @classmethod
    def updateuser(self, update: Update, context: CallbackContext) -> None:
        directory = os.path.dirname(
            os.path.realpath(__file__)) + "\Database\\"
        user_info = update.message.from_user
        if os.path.isfile(f'{directory}Users.sqlite'):
            conn = sqlite3.connect(f'{directory}Users.sqlite')
            cur = conn.cursor()
        else:
            conn = sqlite3.connect(f'{directory}Users.sqlite')
            cur = conn.cursor()
            cur.execute(
                'CREATE TABLE "Users" ("id"	INTEGER,"first_name" TEXT, "last_name" TEXT, "username" TEXT);')

        cur.execute('SELECT id from Users')
        all_id = [x[0] for x in cur.fetchall()]
        if user_info['id'] in all_id:
            pass
        else:
            cur.execute('INSERT INTO Users (id,first_name,last_name,username) VALUES (?,?,?,?);', (
                user_info['id'], user_info['first_name'], user_info['last_name'], user_info['username']))

        conn.commit()

    @classmethod
    def getuser(self, user_id: int) -> None:
        directory = os.path.dirname(os.path.realpath(__file__)) + "\DataBase\\"

        if os.path.isfile(f'{directory}Users.sqlite'):
            conn = sqlite3.connect(f'{directory}Users.sqlite')
            cur = conn.cursor()

            cur.execute(f'SELECT first_name from Users where id = {user_id}')
            first_name = cur.fetchall()
            try:
                return first_name[0][0]
            except IndexError:
                return None
        else:
            return None
