from pydantic import BaseModel

from arx_bank_server.setup import DetectionStatus


class NotFoundError(BaseModel):
    def __init__(self, detail: str = "Not Found"):
        super().__init__()
        self.detail = detail

    detail: str = "Not Found"


class UnauthorizedError(BaseModel):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__()
        self.detail = detail

    detail: str = "Unauthorized"


class DetectionData(BaseModel):
    users: list[str]
    count: int
    timestamp: int
    status: DetectionStatus


class RegisteringData(BaseModel):
    position: str
    frame_captured: int
    frame_total: int
    status: DetectionStatus


class TrainResponse(BaseModel):
    status: str
    user: str


class AlreadyExistsError(BaseModel):
    def __init__(self, detail: str = "Already Exists"):
        super().__init__()
        self.detail = detail

    detail: str = "Already Exists"
