import asyncio
import aiohttp
import lxml.html as HTML
from lxml import etree
import re
import random
from functools import wraps
import datetime
import requests
from time import time
import HHRuStorage
from Exceptions import *
import config
import hashlib


def delay_request(func):
    """
    Decorator, sets a delay for the request
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        timetosleep = random.randint(1, 1000) * 0.003
        print(f"Sleeping for {timetosleep} seconds")
        await asyncio.sleep(timetosleep)
        res = func(*args, **kwargs)
        return res

    return wrapper


def runtime(func):
    """
    Decorator, shows amount of time the function has been running for
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        exectime = time() - start
        print(f"{func.__name__, args[1:]} executed for {exectime} seconds")
        return res

    return wrapper


def runtime_async(func):
    """
    Decorator, shows amount of time the function has been running for
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time()
        res = await func(*args, **kwargs)
        exectime = time() - start
        print(f"{func.__name__, args[1:]} executed for {exectime} seconds")
        return res

    return wrapper


class HHRuParser:
    current_session: None
    first_launch: bool

    def __init__(self):
        self.domain = config.parser_settings["domain"]
        self.user = "Non Authorised"
        self.cookies = None
        self.regexp = {
            "pt_pagescount": re.compile("index(\d+)"),
            "pt_topic404": re.compile("(Тема не указана)|(Не указана Тема)"),

            "pm_userid": re.compile("id(\d+)"),
            "pm_topicid": re.compile("-(\d+)/"),
            "pm_date": re.compile("(\d{1,2}) (\w+) (\d{4}).? ?(\d{2})?:?(\d{2})?"),
            "pm_messageid": re.compile("post(\d+)"),
        }

    @runtime_async
    async def fetch(self, url):
        """
        This function requests the given URL and returns it in a form of lxml.html.HtmlElement object
        :param url: String, containing url to fetch
        :return: HtmlElement
        """
        async with aiohttp.ClientSession() as session:
            if self.cookies:
                session.cookies = self.cookies
            async with session.get(url) as resp:
                return await resp.text()

    def _auth_request(self):
        user = config.forum_account["username"]
        pwd = config.forum_account["password"]
        params = {
            "vb_login_username": user,
            "vb_login_password": pwd,
            "vb_login_md5password": hashlib.md5(pwd.encode()).hexdigest(),
            "vb_login_md5password_utf": hashlib.md5(pwd.encode()).hexdigest(),
            "cookieuser": 1,
            "do": 'login',
            "s": '',
            "securitytoken": 'guest'
        }
        # TODO Тут сделать прокси

        return requests.post(f"https://www.{self.domain}/forum/login.php", data=params)

    def _auth_response_process(self, auth_response):
        if re.search("предел попыток входа", auth_response.text):
            raise ErrorAuthLimit()
        elif re.search("register\.php|login\.php", auth_response.text):
            raise ErrorAuthDataWrong()
        elif re.search(config.forum_account["username"], auth_response.text):
            self.cookies = auth_response.cookies
            return True
        else:
            return None

    def login(self):
        if not (config.forum_account["username"] and
                config.forum_account["password"]):
            raise ErrorAuthDataMissing()
        auth_response = self._auth_request()
        return self._auth_response_process(auth_response)

    @runtime_async
    async def parse_topic(self, current_topic):
        """
        :param current_topic: id of topic to process
        :return: HHRuStorage.Topic
        """

        topic_url = f"https://www.{self.domain}/forum/showthread.php?s=&threadid={current_topic}"
        page = await self.fetch(topic_url)
        page = HTML.document_fromstring(page)

        # TODO Определить, существует тема или нет
        topic_error = page.xpath('.//table[contains(@class, "tborder") and contains(@width, "70%")]')
        # topic_error = re.search("<p>Не указана Тема. ", page)
        # page = HTML.document_fromstring(page)

        if not topic_error:
            last_page_url = page.find_class("pages")
            if last_page_url:
                last_page_url = last_page_url.pop()[-1].attrib["href"]
                pages_count = int(self.regexp["pt_pagescount"].search(last_page_url).group(1))
            else:
                pages_count = 0

            topic_name = page.xpath(".//title/text()").pop()
            print("Current topic name: " + topic_name)

            messages = page.find_class("post_wrap_div")
            tasks = [asyncio.create_task(self.parse_message(msg, current_topic)) for msg in messages]
            await asyncio.wait(tasks)
            messages = []
            for task in tasks:
                messages.append(task.result())

            # TODO Сделать ограничение по вызовам
            tasks = [asyncio.create_task(self._parse_page(current_topic, topic_page))
                     for topic_page in range(2, pages_count + 1)]
            if tasks:
                await asyncio.wait(tasks)

            for task in tasks:
                for msg in task.result():
                    messages.append(msg)
            return HHRuStorage.Topic(current_topic, topic_name, messages, topic_url)
        else:
            topic_error_text = topic_error.pop().text_content()
            page_status = self.regexp["pt_topic404"].search(topic_error_text)

            if page_status.group(1):
                topic_keywords = "DEL/HID: " + page.xpath("head/meta[contains(@name, 'keywords')]")[0].attrib["content"]
                print(f"Тема удалена или скрыта. Возможное название темы: {topic_keywords}")
                return HHRuStorage.Topic(current_topic, topic_keywords, list(), topic_url)
            elif page_status.group(2):
                print(f"Тема еще не создана")
                return None
            else:
                raise Exception("Something went wrong with topic parsing")

    # @delay_request
    # @runtime
    async def _parse_page(self, topic_id, topic_page):
        """
        :param topic_id: id of currently processing topic
        :param topic_page: id of currently processing page
        :return: list of HHRuStorage.Message objects
        """

        page = HTML.document_fromstring(
            await self.fetch(f"https://www.{self.domain}/forum/showthread.php?t={topic_id}&page={topic_page}"))
        messages = page.find_class("post_wrap_div")
        tasks = [asyncio.create_task(self.parse_message(msg, topic_id)) for msg in messages]
        await asyncio.wait(tasks)
        messages = []
        for task in tasks:
            messages.append(task.result())
        return messages

    def _get_date(self, date):
        date = self.regexp["pm_date"].search(date)
        if date.group(4) and date.group(5):
            return datetime.datetime(int(date.group(3)), HHRuStorage.months_strtoint[date.group(2)], int(date.group(1)),
                                     int(date.group(4)), int(date.group(5)),
                                     tzinfo=datetime.timezone(datetime.timedelta(hours=3)))
        else:
            return datetime.date(int(date.group(3)), HHRuStorage.months_strtoint[date.group(2)], int(date.group(1)))

    async def parse_message(self, msg, topic_id=0):
        """
        :param msg: HtmlElement containing block with message to process
        :param topic_id: id of currently processing topic
        :return: HHRuStorage.Message
        """

        username_block = msg.find_class("username").pop()
        # print(etree.tostring(username_block, pretty_print=True))
        try:
            if username_block.getchildren():
                user_name = username_block[0].text_content().strip()
                user_id = int(self.regexp["pm_userid"].search(username_block[0].attrib['href']).group(1))
            else:
                user_name = username_block.text_content().strip()
                user_id = 0
        except AttributeError:
            user_name = etree.tostring(username_block, pretty_print=True)
            user_id = 0
        try:
            if not topic_id:
                topic_block = msg.xpath(".//a[contains('title', 'Прямая Ссылка')]").attrib["href"].text_content()
                topic_id = int(self.regexp["pm_topicid"].search(topic_block).group(1))
        except AttributeError:
            print(topic_id)

        # TODO Доработать парсинг текста сообщения
        message_block = msg.find_class("st_pt_c2")[0]

        message_text = ''.join(message_block.xpath('.//div[contains(@class, "mtext")]/text()'))

        date = message_block.xpath('.//tr/td')[0].text_content().strip()
        date = self._get_date(date)

        post_url = message_block.xpath('.//td/a')[-1].attrib['href']
        message_id = int(self.regexp["pm_messageid"].search(post_url).group(1))

        return HHRuStorage.Message(message_id, topic_id, user_id, user_name, date, message_text, post_url)

    @runtime_async
    async def parse_user(self, user_id):
        """
        This method requests a page with user information on given user id's and returns a HHRuStorage.User object
        :param user_id: Id of processing user
        :return: HHRuStorage.User
        """
        page = HTML.document_fromstring(await self.fetch(f"https://www.{self.domain}/forum/id{user_id}-user"))
        usernames = [page.xpath("head/meta[@name='keywords']/@content").pop().split(',')[0]]
        page = page.find_class("profile").pop()
        username_history = page.find_class("username_history")
        if username_history:
            usernames.extend(username_history.pop().xpath(".//b/text()"))
        usernames = usernames[::-1]

        reg_date = self._get_date(
            page.xpath(".//dt[text()='Регистрация']/following-sibling::dd")[0].text
        )

        views = int(page.find_class("alt2 smallfont block_row block_footer")
                    .pop().xpath("strong/text()").pop().replace(",", ''))
        return HHRuStorage.User(user_id, reg_date, usernames, views)
