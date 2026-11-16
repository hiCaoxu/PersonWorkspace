from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    passcode: str = Field(min_length=1, max_length=128)


class ChangePasscodeRequest(BaseModel):
    old_passcode: str = Field(min_length=1, max_length=128)
    new_passcode: str = Field(min_length=6, max_length=128)


class RevealRequest(BaseModel):
    passcode: str = Field(min_length=1, max_length=128)


class MeResponse(BaseModel):
    owner: str = "owner"
    app_name: str


class RevealTicket(BaseModel):
    ticket: str = Field(min_length=1, max_length=2048)
