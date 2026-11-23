from django.db import models

# Create your models here.

class PatientRecord(models.Model):
    STATUS_CHOICES = [
        ("Aguardando", "Aguardando"),
        ("Em atendimento", "Em atendimento"),
        ("Concluído", "Concluído"),
        ("Cancelado", "Cancelado"),
    ]

    name = models.CharField(max_length=120)
    arrival_time = models.CharField(max_length=5)
    arrival_minutes = models.PositiveSmallIntegerField()
    priority = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Aguardando")

    class Meta:
        db_table = "sigae_patients"
    def __str__(self) -> str:
        return f"#{self.id} {self.name} ({self.status})"   

class DoctorRecord(models.Model):
    STATUS_CHOICES = [
        ("Disponível", "Disponível"),
        ("Em atendimento", "Em atendimento"),
    ]

    name = models.CharField(max_length=120)
    registry_code = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Disponível")
    completed_count = models.PositiveIntegerField(default=0)
    last_assigned_seq = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "sigae_doctors"

    def __str__(self) -> str:
        return f"#{self.id} {self.name} ({self.registry_code})"

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ("Em atendimento", "Em atendimento"),
        ("Concluído", "Concluído"),
        ("Cancelado", "Cancelado"),
    ]

    patient = models.ForeignKey(PatientRecord, on_delete=models.PROTECT, related_name="attendances")
    doctor = models.ForeignKey(DoctorRecord, on_delete=models.PROTECT, related_name="attendances")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Em atendimento")
    started_at = models.CharField(max_length=8)  # "HH:MM:SS"
    finished_at = models.CharField(max_length=8, null=True, blank=True)

    class Meta:
        db_table = "sigae_attendances"

    def __str__(self) -> str:
        return f"Atendimento #{self.id} - Paciente #{self.patient_id} / Médico #{self.doctor_id}"