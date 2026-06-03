from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: str | None = Field(default=None, index=True)
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    role: str = Field(default="user")  # 'admin', 'auditor', 'user'


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class UserUpdate(SQLModel):
    full_name: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None
    role: str | None = None
