from pydantic import BaseModel, EmailStr, Field


class SignupIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class PredictIn(BaseModel):
    analysis_id: int


class NotesIn(BaseModel):
    notes: str = Field(max_length=5000)


class FusionConfigIn(BaseModel):
    w_static: float
    w_behavior: float
    t_suspicious: float
    t_ransomware: float


class RoleIn(BaseModel):
    role: str = Field(pattern="^(admin|analyst|user)$")
    is_active: bool = True
