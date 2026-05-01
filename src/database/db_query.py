from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row
from aiogram.types import User, Chat

from string import ascii_letters, digits
from secrets import choice

from datetime import datetime

import config

characters = ascii_letters + digits + "_"

nonpermissions_letters = 'abefghijklmnopqstvwxyz'
nonpermissions_punctuation = punctuation = r"""!"#$%&'()*+,./:;<=>?@[\]^_`{|}~ """

class OKey(): # Окей :)
    def __init__(self, **kwargs):
        self.key: str = kwargs['key']
        self.permissions: str = kwargs['permissions']
        self.can_create_api_keys: bool = kwargs['can_create_api_keys']
        self.date_reg: datetime = kwargs['date_reg']

class OUser():
    def __init__(self, **kwargs):
        self.id: int = kwargs['id']
        self.type: str = kwargs['type']
        self.title: str = kwargs['title']
        self.first_name: str = kwargs['first_name']
        self.last_name: str = kwargs['last_name']
        self.username: str = kwargs['username']
        self.language_code: str = kwargs['language_code']
        self.owner_id: int = kwargs['owner_id']
        self.zoneinfo: str = kwargs['zoneinfo']
        self.date_reg_db: datetime = kwargs['date_reg_db']

    async def full_name(self):
        if self.type == "private":
            return self.first_name + " " + self.last_name
        self.title

    async def mention(self):
        if self.type == "private":
            return f"<a href='https://t.me/{self.username}'>{self.full_name()}</a>" if self.username else f"<a href='tg://openmessage?user_id={str(self.id).removeprefix("-100")}'>{self.full_name()}</a>"
        return self.title

class Database():
    def __init__(self):
        self.conn = None

    async def connect(self):
        self.conn = await AsyncConnection.connect(
            host        = config.DB_HOST,
            dbname      = config.DB_DBNAME,
            port        = config.DB_PORT,
            user        = config.DB_USER,
            password    = config.DB_PASSWORD,
            row_factory = dict_row
        )

    async def key_mk(self, permissions: str = "-r--", can_create_api_keys: bool = False) -> OKey:
        if len(permissions) != 4:
            raise ValueError("Длинна прав должна быть 4 символа")
        if not set(permissions.casefold()).issubset(set("crud-")):
            raise ValueError("Неверный формат прав. Используйте только 'c','r','u','d' или '-', например '-r--'")
        if can_create_api_keys is None:
            can_create_api_keys = False

        try:
            async with self.conn.cursor() as cur:
                while True:
                    key = "".join(choice(characters) for _ in range(config.API_KEYS_LENGTH))
                    await cur.execute("SELECT 1 FROM api_keys WHERE key = %s", (key,))
                    if not await cur.fetchone():
                        break

                await cur.execute(
                    """INSERT INTO api_keys ("key", permissions, can_create_api_keys) VALUES (%s, %s, %s) RETURNING *""",
                    (key, permissions, can_create_api_keys)
                )
                result = await cur.fetchone()
                await self.conn.commit()
                return OKey(**result)
        except Exception as e:
            print(f"database: mk_key(): {e}")
            await self.conn.rollback()
            return None

    async def key_get(self, key: str) -> OKey:
        try:
            async with self.conn.cursor() as cur:
                await cur.execute('SELECT * FROM api_keys WHERE "key" = %s', (key,))
                result = await cur.fetchone()
                if result is None:
                    return None
                return OKey(**result)
        except Exception as e:
            print(f"database: get_key(): {e}")
            return None


    async def user_mk(self, user: User = None, chat: Chat = None, owner_id: int = None, zoneinfo: str = None) -> OUser:
        if bool(user) == bool(chat):
            raise ValueError("Нужно передать либо user, либо chat")

        if user:
            obj_id = user.id
            obj_type = "private"
            title = None
            first_name = user.first_name
            last_name = user.last_name
            username = user.username
            language_code = user.language_code
        else:
            obj_id = chat.id
            obj_type = chat.type
            title = chat.title
            first_name = None
            last_name = None
            username = chat.username
            language_code = None

        try:
            async with self.conn.cursor() as cur:
                if username is not None:
                    await cur.execute(
                        'UPDATE users SET username = NULL WHERE username = %s AND id != %s',
                        (username, obj_id)
                    )

                await cur.execute(
                    """INSERT INTO users (id, "type", title, first_name, last_name, username, language_code, owner_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET 
                        "type" = EXCLUDED."type",
                        title = EXCLUDED.title,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        username = EXCLUDED.username,
                        language_code = COALESCE(EXCLUDED.language_code, users.language_code),
                        owner_id = COALESCE(EXCLUDED.owner_id, users.owner_id)
                    RETURNING *""",
                    (obj_id, obj_type, title, first_name, last_name, username, language_code, owner_id)
                )
                result = await cur.fetchone()
                await self.conn.commit()
                return OUser(**result)
        except Exception as e:
            print(f"database: user_mk(): {e}")
            await self.conn.rollback()
            return None

    async def user_get(self, **kwargs) -> OUser:
        if not kwargs:
            return None

        try:
            conditions = []
            params = []

            for column, value in kwargs.items():
                condition = sql.SQL("{} = %s").format(sql.Identifier(column))
                conditions.append(condition)
                params.append(value)

            query = sql.SQL("SELECT * FROM users WHERE {where_clause}").format(
                where_clause=sql.SQL(" AND ").join(conditions)
            )

            async with self.conn.cursor() as cur:
                await cur.execute(query, params)
                result = await cur.fetchone()
                if result is None:
                    return None
                return OUser(**result)
        except Exception as e:
            print(f"database: get_user(): {e}")
            return None

    async def user_rm(self, user_id: int) -> bool:
        try:
            async with self.conn.cursor() as cur:
                await cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

                if cur.rowcount == 0:
                    return False                

                await self.conn.commit()
                return True
        except Exception as e:
            print(f"database: user_rm(): {e}")
            await self.conn.rollback()
            return False