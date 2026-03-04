__all__ = ["UserFields"]

from typing import Annotated
from uuid import UUID

from pydantic import Field


class UserFields:
    ID = Annotated[UUID, Field(description="ID пользователя")]
    Name = Annotated[
        str, Field(description="Имя пользователя", max_length=100, examples=["Иван Иванов"])]
    Email = Annotated[str, Field(
        description="Email пользователя", max_length=100, examples=["example@gmail.com"]
    )]
