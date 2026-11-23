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
