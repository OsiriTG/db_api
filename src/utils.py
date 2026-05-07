from config import *
from fastapi import HTTPException

async def get_key_and_check_permission(api_key: str, required_char: str = "-"):
    key_data = await db.read_key(api_key)
    if key_data is None:
        raise HTTPException(status_code=401, detail="Неверный API-ключ")

    required_chars = [char for char in required_char if char != "-"]

    if required_chars:
        user_permissions = set(key_data.permissions)
        missing = [perm for perm in required_chars if perm not in user_permissions]
        if missing:
            raise HTTPException(
                status_code=403, 
                detail=(
                    f"У вашего ключа нет прав: {', '.join(missing)}. "
                    f"Требуется полный набор: {''.join(required_chars)}"
                )
            )

    return key_data
