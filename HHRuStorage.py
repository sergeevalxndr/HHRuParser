"""
Contains the classes of the main entities of the forum.
"""

class Message:
    def __init__(self, message_id="", topic_id="", user_id="", user_name="", date="", content="", url=""):
        self.message_id = message_id
        self.topic_id = topic_id
        self.user_id = user_id
        self.user_name = user_name
        self.date = date
        self.content = content
        self.url = url

    def __str__(self):
        return (f'Date: {self.date}\n'
                f'Username: {self.user_name} (id{self.user_id})\n'
                f'Message id{self.message_id} in topic{self.topic_id}: \n{self.content}\n'
                f'Message URL: {self.url}')

    def __repr__(self):
        return f"Message({self.message_id}, {self.topic_id}, {self.user_id}, " \
               f"{self.user_name}, {self.date}, {self.content}, {self.url})"

    def get(self):
        return self.message_id, self.topic_id, self.user_id, self.user_name, \
               self.date, self.content, self.url


class Topic:
    def __init__(self, id="", name="", messages="", url=""):
        self.id = id
        self.name = name
        self.messages = messages
        self.url = url

    def __str__(self):
        return (f'Topic id{self.id}: {self.name}\n'
                f'Author: id{self.messages[0].user_id} {self.messages[0].user_name}\n'
                f'Count of messages: {len(self.messages)}\n'
                f'Topic URL: {self.url}')

    def get(self):
        return self.id, self.name, self.url


class User:
    def __init__(self, user_id="", reg_date="", names=[""], views=""):
        self.user_id = user_id
        self.reg_date = reg_date
        self.names = names
        self.views = views

    def __str__(self):
        return (f'Username: {self.names[-1].strip()} (id{self.user_id})\n'
                f'Registration date: {self.reg_date}\n'
                f'Profile views: {self.views}')

    def get(self):
        return self.user_id, self.reg_date, self.names, self.views


months_strtoint = {
    "Января": 1,
    "Февраля": 2,
    "Марта": 3,
    "Апреля": 4,
    "Мая": 5,
    "Июня": 6,
    "Июля": 7,
    "Августа": 8,
    "Сентября": 9,
    "Октября": 10,
    "Ноября": 11,
    "Декабря": 12
}
