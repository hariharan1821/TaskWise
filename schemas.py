from typing import Optional
from pydantic import BaseModel

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: int

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    owner_id: Optional[int] = None

    model_config = {
    "from_attributes": True
}


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    model_config = {
    "from_attributes": True
}