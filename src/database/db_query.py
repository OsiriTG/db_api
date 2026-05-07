from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row
from aiogram.types import User, Chat

from string import ascii_letters, digits
from secrets import choice
from datetime import datetime

import config

base64 = ascii_letters + digits + "_" + "-"

nonpermissions_letters = 'abefghijklmnopqstvwxyz'
nonpermissions_punctuation = punctuation = r"""!"#$%&'()*+,./:;<=>?@[\]^_`{|}~ """


class OKey(): # Окей :)
    def __init__(self, **kwargs):
        self.key: str = kwargs['key']
        self.permissions: str = kwargs['permissions']
        self.can_create_api_keys: bool = kwargs['can_create_api_keys']
        self.owner_id: int | None = kwargs['owner_id']
        self.date_reg: datetime = kwargs['date_reg']

class OUser():
    def __init__(self, **kwargs):
        self.id: int = kwargs['id']
        self.is_bot: bool = kwargs['is_bot']
        self.type: str = kwargs['type']
        self.title: str | None = kwargs['title']
        self.first_name: str | None = kwargs['first_name']
        self.last_name: str | None = kwargs['last_name']
        self.username: str | None = kwargs['username']
        self.language_code: str | None = kwargs['language_code']
        self.is_premium: bool = kwargs['is_premium']

        self.shifted_id: int = kwargs['shifted_id']
        if self.first_name and self.last_name:
            self.full_name: str | None = self.first_name + " " + self.last_name
        elif self.first_name:
            self.full_name: str | None = self.first_name
        else:
            self.full_name: str | None = None
        if self.type == "private":
            self.mention: str = f"<a href='https://t.me/{self.username}'>{self.first_name}</a>" if self.username else f"<a href='tg://openmessage?user_id={self.id}'>{self.first_name}</a>"
        else:
            self.mention: str = f"<a href='https://t.me/{self.username}'>{self.title}</a>" if self.username else self.title

        self.oid: str = kwargs['oid']
        self.owner_id: int = kwargs['owner_id']
        self.zoneinfo: str = kwargs['zoneinfo']
        self.date_reg_db: datetime = kwargs['date_reg_db']


class DbQuery():
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

    async def create_key(self, permissions: str = "-r--", can_create_api_keys: bool = False, owner_id: int = None) -> OKey:
        if len(permissions) != 4 or not set(permissions.casefold()).issubset(set("crud-")):
            return None
        if can_create_api_keys is None:
            can_create_api_keys = False

        try:
            async with self.conn.cursor() as cur:
                while True:
                    key = "".join(choice(base64) for _ in range(config.API_KEYS_LENGTH))
                    await cur.execute("SELECT 1 FROM api_keys WHERE key = %s", (key,))
                    if not await cur.fetchone():
                        break

                await cur.execute("SELECT 1 FROM users WHERE id = %s", (owner_id,))
                if not await cur.fetchone():
                    owner_id = None

                await cur.execute(
                    """INSERT INTO api_keys ("key", permissions, can_create_api_keys, owner_id) VALUES (%s, %s, %s, %s) RETURNING *""",
                    (key, permissions, can_create_api_keys, owner_id)
                )
                result = await cur.fetchone()
                await self.conn.commit()
                return OKey(**result)
        except Exception as e:
            print(f"database: create_key(): {e}")
            await self.conn.rollback()
            return None

    async def read_key(self, key: str) -> OKey:
        try:
            async with self.conn.cursor() as cur:
                await cur.execute('SELECT * FROM api_keys WHERE "key" = %s', (key,))
                result = await cur.fetchone()
                if result is None:
                    return None
                return OKey(**result)
        except Exception as e:
            print(f"database: read_key(): {e}")
            return None


    async def create_user(self, user: User = None, chat: Chat = None, owner_id: int = None, zoneinfo: str = None) -> OUser:
        if bool(user) == bool(chat):
            return None

        oid = None

        if user:
            obj_id = user.id
            is_bot = user.is_bot
            obj_type = "private"
            title = None
            first_name = user.first_name
            last_name = user.last_name
            username = user.username
            language_code = user.language_code
            is_premium = user.is_premium
            shifted_id = obj_id
            owner_id = None
        else:
            obj_id = chat.id
            is_bot = False
            obj_type = chat.type
            title = chat.title
            first_name = chat.first_name
            last_name = chat.last_name
            username = chat.username
            language_code = None
            is_premium = False
            shifted_id = chat.shifted_id

        try:
            async with self.conn.cursor() as cur:
                if username is not None:
                    await cur.execute(
                        'UPDATE users SET username = NULL WHERE username = %s AND id != %s',
                        (username, obj_id)
                    )

                await cur.execute("SELECT oid FROM users WHERE id = %s", (owner_id,))
                result_user = await cur.fetchone()
                if owner_id is not None and not result_user:
                    owner_id = None
                if result_user and result_user['oid']:
                    oid = result_user['oid']
                else:
                    while True:
                        oid = "".join(choice(base64) for _ in range(config.DB_OID_LENGTH))
                        await cur.execute("SELECT 1 FROM users WHERE oid = %s", (oid,))
                        if not await cur.fetchone():
                            break

                await cur.execute(
                    """INSERT INTO users (id, is_bot, "type", title, first_name, last_name, username, language_code, is_premium, shifted_id, "oid", owner_id, zoneinfo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET 
                        is_bot = EXCLUDED.is_bot,
                        "type" = EXCLUDED."type",
                        title = EXCLUDED.title,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        username = EXCLUDED.username,
                        language_code = EXCLUDED.language_code,
                        is_premium = EXCLUDED.is_premium,
                        shifted_id = EXCLUDED.shifted_id,
                        "oid" = COALESCE(users."oid", EXCLUDED."oid"),
                        owner_id = COALESCE(EXCLUDED.owner_id, users.owner_id),
                        zoneinfo = COALESCE(EXCLUDED.zoneinfo, users.zoneinfo)
                    RETURNING *""",
                    (obj_id, is_bot, obj_type, title, first_name, last_name, username, language_code, is_premium, shifted_id, oid, owner_id, zoneinfo)
                )
                result = await cur.fetchone()
                await self.conn.commit()
                return OUser(**result)
        except Exception as e:
            print(f"database: create_user(): {e}")
            await self.conn.rollback()
            return None

    async def read_user(self, **kwargs) -> OUser:
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
            print(f"database: read_user(): {e}")
            return None

    async def delete_user(self, user_id: int) -> bool:
        try:
            async with self.conn.cursor() as cur:
                await cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

                if cur.rowcount == 0:
                    return False                

                await self.conn.commit()
                return True
        except Exception as e:
            print(f"database: delete_user(): {e}")
            await self.conn.rollback()
            return None