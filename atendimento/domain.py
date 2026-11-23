from datetime import datetime

PRIORITY_LABELS = {
    1: "Emergência",
    2: "Muito urgente",
    3: "Urgente",
    4: "Pouco urgente",
    5: "Não urgente",
}


class Patient:
    __slots__ = (
        "id",
        "name",
        "arrival_time",
        "arrival_minutes",
        "priority",
        "status",
        "heap_index",
        "rb_node",
    )

    def __init__(self, patient_id: int, name: str, arrival_time: str, arrival_minutes: int, priority: int, status: str = "Aguardando"):
        self.id = patient_id
        self.name = name
        self.arrival_time = arrival_time
        self.arrival_minutes = arrival_minutes
        self.priority = priority
        self.status = status
        self.heap_index: int = -1
        self.rb_node = None

    def to_dict(self) -> dict:
        label = PRIORITY_LABELS[self.priority] if 1 <= self.priority <= 5 else ""
        return {
            "id": self.id,
            "name": self.name,
            "arrival_time": self.arrival_time,
            "arrival_minutes": self.arrival_minutes,
            "priority": self.priority,
            "priority_label": label,
            "status": self.status,
        }
class Doctor:
    __slots__ = (
        "id",
        "name",
        "registry_code",
        "status",
        "completed_count",
        "last_assigned_seq",
        "heap_index"
    )

    def __init__(self, doctor_id: int, name: str, registry_code: str, status: str = "Disponível", completed_count: int = 0, last_assigned_seq: int = 0):
        self.id = doctor_id
        self.name = name
        self.registry_code = registry_code
        self.status = status
        self.completed_count = completed_count
        self.last_assigned_seq = last_assigned_seq
        self.heap_index: int = -1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "registry_code": self.registry_code,
            "status": self.status,
            "completed_count": self.completed_count,
            "last_assigned_seq": self.last_assigned_seq,
        }

class Attendance:
    __slots__ = (
        "id",
        "patient",
        "doctor",
        "status",
        "started_at",
        "finished_at"
    )
    def __init__(self, attendance_id: int, patient: Patient, doctor: Doctor, status: str = "Em atendimento", started_at: str | None = None, finished_at: str | None = None):
        self.id = attendance_id
        self.patient = patient
        self.doctor = doctor
        self.status = status
        self.started_at = started_at or datetime.now().strftime("%H:%M:%S")
        self.finished_at = finished_at
        
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient": self.patient.to_dict(),
            "doctor": self.doctor.to_dict(),
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

