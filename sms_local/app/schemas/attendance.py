from pydantic import BaseModel
from datetime import date

class AttendanceMarkIn(BaseModel):
    student_id: str
    date: date
    code: str  # P/A/L/E

class AttendanceDailyOut(BaseModel):
    student_id: str
    code: str
