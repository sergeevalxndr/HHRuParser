import psycopg2
from functools import wraps


class DBInterface:
    def __init__(self, db_name="", host_name="", username="", password=""):
        self.db_name = db_name
        self.host_name = host_name
        self.username = username
        self.password = password
        self.connection = None

        # TODO Ключи бд и пр., доработать таблицы
        self.tables = [{"name": "messages", "query": "CREATE TABLE messages (id integer, topic_id integer, "
                                                     "user_id integer, user_name text, "
                                                     "content text, date timestamptz, url text)"},
                       {"name": "users", "query": "CREATE TABLE users (id integer, reg_date date, "
                                                  "names text [], views integer)"},
                       {"name": "topics", "query": "CREATE TABLE topics (id integer, name text, url text)"}, ]

    def __repr__(self):
        return (f'\nDB_Name: {self.db_name}\n'
                f'Host name: {self.host_name}\n'
                f'Username: {self.username}\n'
                f'Password: {self.password}')

    class Decorators:
        @classmethod
        def connect_to_dbms(cls, func):
            """
            Establishes a connection to a database management system for creating or dropping a table.
            """
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                temp_connection = self.connection
                self.connection = psycopg2.connect(
                    host=self.host_name,
                    user=self.username,
                    password=self.password)
                self.connection.autocommit = True
                res = func(self, *args, **kwargs)

                self.connection.close()
                self.connection = temp_connection
                return res

            return wrapper

        @classmethod
        def connect_to_db(cls, func):
            """
            Establishes a connection to the database. Used when needed to create, modify or select a table.
            """
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                temp_connection = self.connection
                self.connection = psycopg2.connect(
                    host=self.host_name,
                    dbname=self.db_name,
                    user=self.username,
                    password=self.password)
                self.connection.autocommit = True
                res = func(self, *args, **kwargs)

                self.connection.close()
                self.connection = temp_connection
                return res

            return wrapper

    @Decorators.connect_to_dbms
    def drop_db(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"REVOKE CONNECT ON DATABASE {self.db_name} FROM PUBLIC, {self.username};")
                cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                               f"where pid <> pg_backend_pid() AND datname = '{self.db_name}'")
                cursor.execute(f"DROP DATABASE {self.db_name}")
                print("Database was successfully dropped!")
        except psycopg2.Error as error:
            print("DBInterface.drop_db " + error.pgerror)

    @Decorators.connect_to_dbms
    def create_db(self):
        db_errors = []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE {self.db_name}")
                print(f"Database {self.db_name} was successfully created!")
        except psycopg2.ProgrammingError as error:
            db_errors.append(error.pgerror)

        for table in self.tables:
            error_message = self.create_table(table)
            if error_message:
                db_errors.append(error_message)

        if db_errors:
            for error_message in db_errors:
                print(error_message.strip())
            return False
        else:
            return True

    @Decorators.connect_to_db
    def create_table(self, table: dict):
        """

        :param table: A dict() with two string values: [name] and [query]
        :return:
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(table["query"])
                print(f"Table {table['name']} was successfully created!")
                return None

        except psycopg2.ProgrammingError as error:
            if error.pgcode == "42P07":
                return error.pgerror
            else:
                return psycopg2.NotSupportedError

    @Decorators.connect_to_db
    def add_message(self, message_id=0, topic_id=0, user_id=0, user_name="", date="", content="", url=""):
        """
        Adds a message to a PostgreSQL database
        :return: True, if the element was added successfully. Otherwise false.
        """
        try:
            with self.connection.cursor() as cursor:
                sql_query = "INSERT INTO messages (id, topic_id, user_id, user_name, date, content, url) " \
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                parameters = (message_id, topic_id, user_id, user_name, date, content, url)
                cursor.execute(sql_query, parameters)
            print(f"Message id{message_id} was added into the database!")
            return True
        except psycopg2.ProgrammingError as error:
            print("DBInterface.add_message " + error.pgerror)
            return False

    @Decorators.connect_to_db
    def add_topic(self, topic_id=0, name="", url=""):
        try:
            with self.connection.cursor() as cursor:
                sql_query = "INSERT INTO topics (id, name, url) VALUES (%s, %s, %s)"
                parameters = (topic_id, name, url)
                cursor.execute(sql_query, parameters)
            print(f"Topic id{topic_id} was added into the database!")
            return True
        except psycopg2.ProgrammingError as error:
            print("DBInterface.add_topic " + error.pgerror)
            return False

    @Decorators.connect_to_db
    def update_topic(self):
        # TODO update topic
        pass

    @Decorators.connect_to_db
    def show_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM messages")
            result = cursor.fetchall()
            for line in result:
                print(line)
