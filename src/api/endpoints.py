from fastapi import APIRouter, HTTPException, Header
from aiogram.types import User, Chat

from pydantic import BaseModel, Field
from typing import Optional, Any

from config import *
from utils import *

router = APIRouter()


class KeyCreateRequest(BaseModel):
    permissions: str = Field(..., min_length=4, max_length=4, pattern=r"^[crud\-]{4}$")
    can_create_api_keys: bool = False

class TelegramUserIn(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None

class TelegramChatIn(BaseModel):
    id: int
    type: str
    title: str
    username: Optional[str] = None

class UserUpsertRequest(BaseModel):
    user: Optional[TelegramUserIn] = None
    chat: Optional[TelegramChatIn] = None
    owner_id: Optional[int] = None
    zoneinfo: Optional[str] = None


@router.post("/key_mk")
async def key_mk(request: KeyCreateRequest, api_key: str = Header(..., alias="X-API-Key")):
    sender_key_data = await get_key_and_check_permission(api_key)

    if not sender_key_data.can_create_api_keys:
        raise HTTPException(status_code=403, detail="У Вас нет прав создавать новые API-ключи")

    missing_perms = set(request.permissions) - set(sender_key_data.permissions); missing_perms.discard("-")
    if missing_perms:
        raise HTTPException(
            status_code=403, 
            detail=f"Нельзя создать ключ с правами, которых нет у Вас. Вам не хватает: {", ".join(missing_perms)}"
        )

    new_key = await db.key_mk(request.permissions, request.can_create_api_keys)
    if new_key is None:
        raise HTTPException(status_code=500, detail="Непредвиденная ошибка (БД)")

    return {
        "key": new_key.key,
        "permissions": new_key.permissions,
        "can_create_api_keys": new_key.can_create_api_keys,
        "date_reg": new_key.date_reg
    }

@router.get("/")
async def key_get(api_key: str = Header(..., alias="X-API-Key")):
    key_data = await get_key_and_check_permission(api_key)
    return {
        "is_key_exist": True,
        "permissions": key_data.permissions,
        "can_create_api_keys": key_data.can_create_api_keys,
        "date_reg": key_data.date_reg
    }


@router.post("/user_mk")
async def user_mk(request: UserUpsertRequest, api_key: str = Header(..., alias="X-API-Key")):
    await get_key_and_check_permission(api_key, "cu")

    tg_user = User(**request.user.model_dump()) if request.user else None
    tg_chat = Chat(**request.chat.model_dump()) if request.chat else None

    result = await db.user_mk(
        user=tg_user,
        chat=tg_chat,
        owner_id=request.owner_id,
        zoneinfo=request.zoneinfo
    )
    if result is None:
        raise HTTPException(status_code=500, detail="Непредвиденная ошибка (БД)")
        
    return {"status": True, "date_reg_db": result.date_reg_db}

@router.get("/users/{user_id}")
async def user_get(user_id: int, api_key: str = Header(..., alias="X-API-Key")):
    await get_key_and_check_permission(api_key, "r")

    user_data = await db.user_get(id=user_id)
    if user_data is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {
        "id": user_data.id,
        "type": user_data.type,
        "title": user_data.title,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "username": user_data.username,
        "language_code": user_data.language_code,
        "owner_id": user_data.owner_id,
        "zoneinfo": user_data.zoneinfo,
        "date_reg_db": user_data.date_reg_db,
        "full_name": await user_data.full_name(),
        "mention": await user_data.mention()
    }

@router.delete("/user_rm")
async def user_rm(user_id: int, api_key: str = Header(..., alias="X-API-Key")):
    await get_key_and_check_permission(api_key, "d")
    
    result = await db.user_rm(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден в базе")
        
    return {"status": True, "id": user_id}