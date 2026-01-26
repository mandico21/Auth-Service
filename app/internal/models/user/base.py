__all__ = ["UserFields"]

from typing import Annotated

from pydantic import Field


class UserFields:
    ID = Annotated[int, Field(description="ID пользователя", examples=[1])]
    Name = Annotated[
        str, Field(description="Имя пользователя", max_length=100, examples=["Иван Иванов"])]
    Email = Annotated[str, Field(
        description="Email пользователя", max_length=100, examples=["example@gmail.com"]
    )]
