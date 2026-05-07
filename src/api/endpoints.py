from fastapi import APIRouter, HTTPException, Header
from aiogram.types import User, Chat

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from config import *
from utils import *

router = APIRouter()


class KeyCreateRequest(BaseModel):
    permissions: str = Field(..., min_length=4, max_length=4, pattern=r"^[crud\-]{4}$")
    can_create_api_keys: bool = False

class TelegramUserIn(BaseModel):
    id: int
    is_bot: Optional[bool] = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = False

class TelegramChatIn(BaseModel):
    id: int
    type: str
    title: str
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    shifted_id: int

class UserCreateRequest(BaseModel):
    user: Optional[TelegramUserIn] = None
    chat: Optional[TelegramChatIn] = None
    owner_id: Optional[int] = None
    zoneinfo: Optional[str] = None


@router.post("/key_mk")
async def key_mk(request: KeyCreateRequest, api_key: str = Header(..., alias="X-API-Key")):
    sender_key_data = await get_key_and_check_permission(api_key, "c")

    if not sender_key_data.can_create_api_keys:
        raise HTTPException(status_code=403, detail="У Вас нет прав создавать новые API-ключи")

    missing_perms = set(request.permissions) - set(sender_key_data.permissions); missing_perms.discard("-")
    if missing_perms:
        raise HTTPException(
            status_code=403, 
            detail=f"Нельзя создать ключ с правами, которых нет у Вас. Вам не хватает: {", ".join(missing_perms)}"
        )

    new_key = await db.create_key(request.permissions, request.can_create_api_keys)
    if new_key is None:
        raise HTTPException(status_code=500, detail="Непредвиденная ошибка (БД)")

    return {
        "key": new_key.key,
        "permissions": new_key.permissions,
        "can_create_api_keys": new_key.can_create_api_keys,
        "date_reg": new_key.date_reg
    }

@router.get("/{target_api_key}")
async def key_get(target_api_key: str, sender_api_key: str = Header(..., alias="X-API-Key")):
    await get_key_and_check_permission(sender_api_key, "r")

    key_data = await db.read_key(target_api_key)
    if key_data is None:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    return {
        "is_key_exist": True,
        "permissions": key_data.permissions,
        "can_create_api_keys": key_data.can_create_api_keys,
        "date_reg": key_data.date_reg
    }


@router.post("/user_mk")
async def user_mk(request: UserCreateRequest, api_key: str = Header(..., alias="X-API-Key")):
    await get_key_and_check_permission(api_key, "cu")

    tg_user = User(**request.user.model_dump()) if request.user else None
    tg_chat = Chat(**request.chat.model_dump()) if request.chat else None

    user = await db.create_user(
        user=tg_user,
        chat=tg_chat,
        owner_id=request.owner_id,
        zoneinfo=request.zoneinfo
    )
    if user is None:
        raise HTTPException(status_code=500, detail="Непредвиденная ошибка (БД). Попробуйте позже")

    return {
        "id": user.id,
        "is_bot": user.is_bot,
        "type": user.type,
        "title": user.title,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "language_code": user.language_code,
        "is_premium": user.is_premium,
        "shifted_id": user.shifted_id,
        "full_name": user.full_name,
        "mention": user.mention,
        "oid": user.oid,
        "owner_id": user.owner_id,
        "zoneinfo": user.zoneinfo,
        "date_reg_db": user.date_reg_db
    }

@router.get("/users/{user_id}")
async def user_get(user_id: int, api_key: str = Header(..., alias="X-API-Key")):
    await get_key_and_check_permission(api_key, "r")

    user = await db.read_user(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Не удалось найти пользователя")

    return {
        "id": user.id,
        "is_bot": user.is_bot,
        "type": user.type,
        "title": user.title,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "language_code": user.language_code,
        "is_premium": user.is_premium,
        "shifted_id": user.shifted_id,
        "full_name": user.full_name,
        "mention": user.mention,
        "oid": user.oid,
        "owner_id": user.owner_id,
        "zoneinfo": user.zoneinfo,
        "date_reg_db": user.date_reg_db
    }

@router.delete("/user_rm")
async def user_rm(user_id: int, api_key: str = Header(..., alias="X-API-Key")):
    await get_key_and_check_permission(api_key, "d")
    
    result = await db.delete_user(user_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Непредвиденная ошибка (БД). Попробуйте позже")
    if not result:
        raise HTTPException(status_code=404, detail="Такого пользователя не существует")

    return {"status": True, "id": user_id, "timestamp": datetime.now().timestamp()}