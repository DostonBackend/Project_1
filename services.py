from db import Database
from exceptions import BadRequestException
from models import User
from utils import make_password, match_password


class AuthService:

    def __init__(self):
        self.database = Database()
        super().__init__()

    def register_user(self, user: User):
        if self.database.check_username_unique(user.username):
            user.password = make_password(password=user.password)
            self.database.insert_user(**user.__dict__)
        else:
            raise BadRequestException(f"{user.username} username already registered")

    def login_user(self, username, password):
        data = self.database.get_user_by_username(username)
        user = User(username=data[1], password=data[2], email=data[3], phone=data[4])
        user.id = data[0]
        if match_password(password=password, hashed_password=user.password):
            return user
        else:
            raise BadRequestException("Password is not correct")


class TodoService:
    def __init__(self, user):
        self.user = user
        self.database = Database()

    def create_todo(self, title):
        self.database.insert_todo(title=title, status="todo", owner_id=self.user.id)

    def update_todo(self, todo_id, value):
        self.database.update_todo(todo_id=todo_id, value=value)

    def my_todos(self):
        data = self.database.my_todos(self.user.id)
        return data

    def delete_todo(self, todo_id):
        self.database.delete_todo(todo_id=todo_id)


# ------------------

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv("path/to/your/.env")  # O'z .env faylingiz joylashgan joyni ko'rsating


class Database:
    def __init__(self):
        self.db = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            dbname=os.getenv("POSTGRES_DB"),
            password=os.getenv("POSTGRES_PASSWORD"),
            user=os.getenv("POSTGRES_USER"),
            port=os.getenv("POSTGRES_PORT")  # optional: default is 5432
        )
        self.db.autocommit = True

    def create_user_table(self):
        cursor = self.db.cursor()
        create_user_sql = """
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                username VARCHAR(128) UNIQUE NOT NULL,
                password VARCHAR(128) NOT NULL,
                email VARCHAR(56),
                phone VARCHAR(56)
            );
        """
        cursor.execute(create_user_sql)
        self.db.commit()

    def create_todo_table(self):
        cursor = self.db.cursor()
        create_todo_sql = """
            CREATE TABLE IF NOT EXISTS todo(
                id SERIAL PRIMARY KEY,
                title VARCHAR(128) UNIQUE NOT NULL,
                status VARCHAR(128) NOT NULL,
                owner_id INT REFERENCES users(id),
                deadline TIMESTAMP DEFAULT now() + INTERVAL '1 day'
            );
        """
        cursor.execute(create_todo_sql)
        self.db.commit()

    def insert_user(self, username, password, email, phone):
        insert_user_sql = """
            INSERT INTO users(username, password, email, phone) VALUES (%s, %s, %s, %s);
        """
        cursor = self.db.cursor()
        cursor.execute(insert_user_sql, (username, password, email, phone))
        self.db.commit()

    def insert_todo(self, title, status, owner_id):
        insert_todo_sql = """
            INSERT INTO todo(title, status, owner_id) VALUES (%s, %s, %s);
        """
        cursor = self.db.cursor()
        cursor.execute(insert_todo_sql, (title, status, owner_id))
        self.db.commit()

    def check_username_unique(self, username):
        search_username_unique_sql = """
            SELECT * FROM users WHERE username=%s;
        """
        cursor = self.db.cursor()
        cursor.execute(search_username_unique_sql, (username,))
        result = cursor.fetchall()
        self.db.commit()
        if result:
            return False
        else:
            return True

    def get_user_by_username(self, username):
        search_username_sql = """
            SELECT * FROM users WHERE username=%s;
        """
        cursor = self.db.cursor()
        cursor.execute(search_username_sql, (username,))
        result = cursor.fetchone()
        return result

    def update_todo(self, todo_id, value, user_id):
        update_todo_sql = """
            UPDATE todo SET status=%s WHERE id=%s AND owner_id=%s;
        """
        cursor = self.db.cursor()
        cursor.execute(update_todo_sql, (value, todo_id, user_id))
        self.db.commit()

    def delete_todo(self, todo_id, user_id):
        delete_todo_sql = """
            DELETE FROM todo WHERE id=%s AND owner_id=%s;
        """
        cursor = self.db.cursor()
        cursor.execute(delete_todo_sql, (todo_id, user_id))
        self.db.commit()

    def update_todo_title(self, todo_id, title, user_id):
        update_todo_title_sql = """
            UPDATE todo SET title=%s WHERE id=%s AND owner_id=%s;
        """
        cursor = self.db.cursor()
        cursor.execute(update_todo_title_sql, (title, todo_id, user_id))
        self.db.commit()

    def my_todos(self, user_id):
        my_todo_sql = "SELECT * FROM todo WHERE owner_id=%s"
        cursor = self.db.cursor()
        cursor.execute(my_todo_sql, (user_id,))
        data = cursor.fetchall()
        self.db.commit()
        return data
