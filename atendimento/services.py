import threading
from datetime import datetime
from django.db import DatabaseError, IntegrityError, transaction
from .engine import SigaeEngine, _is_valid_priority, format_minutes_hhmm, parse_arrival_minutes
from .models import AttendanceRecord, DoctorRecord, PatientRecord


_lock = threading.RLock()
_engine = SigaeEngine()
_hydrated = False


def _invalidate_cache() -> None:
    global _hydrated
    _engine.clear()
    _hydrated = False


def _ensure_hydrated() -> None:
    global _hydrated
    if _hydrated:
        return
    _engine.clear()
    for row in DoctorRecord.objects.order_by("id").all():
        _engine.hydrate_doctor(
            doctor_id=row.id,
            name=row.name,
            registry_code=row.registry_code,
            status=row.status,
            completed_count=row.completed_count,
            last_assigned_seq=row.last_assigned_seq
        )
    for row in PatientRecord.objects.order_by("id").all():
        _engine.hydrate_patient(
            patient_id=row.id,
            name=row.name,
            arrival_time=row.arrival_time,
            arrival_minutes=row.arrival_minutes,
            priority=row.priority,
            status=row.status
        )
    for row in AttendanceRecord.objects.order_by("id").all():
        _engine.hydrate_attendance(
            attendance_id=row.id,
            patient_id=row.patient_id,
            doctor_id=row.doctor_id,
            status=row.status,
            started_at=row.started_at,
            finished_at=row.finished_at
        )
    _hydrated = True


def reset_engine_cache() -> None:
    with _lock:
        _invalidate_cache()


def get_snapshot() -> dict:
    with _lock:
        _ensure_hydrated()
        return _engine.get_snapshot()


def validate_all() -> bool:
    with _lock:
        _ensure_hydrated()
        return _engine.validate_all()


def register_patient(name: str, arrival_time: str, priority: int) -> dict:
    clean_name = str(name).strip()
    if len(clean_name) < 2 or len(clean_name) > 120:
        raise ValueError("Informe um nome válido (2 a 120 caracteres).")
    if not _is_valid_priority(priority):
        raise ValueError("Classificação de risco deve estar entre 1 e 5.")

    arrival_minutes = parse_arrival_minutes(arrival_time)

    normalized_time = format_minutes_hhmm(arrival_minutes)

    with _lock:
        _ensure_hydrated()
        try:
            with transaction.atomic():
                record = PatientRecord.objects.create(
                    name=clean_name,
                    arrival_time=normalized_time,
                    arrival_minutes=arrival_minutes,
                    priority=priority,
                    status="Aguardando"
                )
                patient = _engine.register_patient(
                    patient_id=record.id,
                    name=record.name,
                    arrival_time=normalized_time,
                    priority=record.priority
                )
                return patient.to_dict()
        except DatabaseError:
            _invalidate_cache()
            raise


def search_patient(patient_id: int) -> dict | None:
    with _lock:
        _ensure_hydrated()
        patient = _engine.get_patient(patient_id)
        return patient.to_dict() if patient else None


def search_waiting_by_arrival(arrival_time: str, patient_id: int) -> dict | None:
    with _lock:
        _ensure_hydrated()
        patient = _engine.search_waiting_by_arrival(arrival_time, patient_id)
        return patient.to_dict() if patient else None


def reclassify_patient(patient_id: int, new_priority: int) -> dict:
    if not _is_valid_priority(new_priority):
        raise ValueError("Nova classificação de risco deve estar entre 1 e 5.")
    with _lock:
        _ensure_hydrated()
        try:
            with transaction.atomic():
                patient = _engine.reclassify_patient(patient_id, new_priority)
                PatientRecord.objects.filter(id=patient.id).update(
                    priority=patient.priority)
                return patient.to_dict()
        except DatabaseError:
            _invalidate_cache()
            raise


def cancel_waiting_patient(patient_id: int) -> dict:
    with _lock:
        _ensure_hydrated()
        try:
            with transaction.atomic():
                patient = _engine.cancel_waiting_patient(patient_id)
                PatientRecord.objects.filter(
                    id=patient.id).update(status="Cancelado")
                return patient.to_dict()
        except DatabaseError:
            _invalidate_cache()
            raise


def register_doctor(name: str, registry_code: str) -> dict:
    clean_name = str(name).strip()
    clean_reg = str(registry_code).strip()
    if len(clean_name) < 2 or len(clean_name) > 120:
        raise ValueError(
            "Informe um nome de médico válido (2 a 120 caracteres).")
    if len(clean_reg) < 3 or len(clean_reg) > 40:
        raise ValueError("Informe um registro profissional fictício válido.")
    with _lock:
        _ensure_hydrated()
        reg_upper = clean_reg.upper()
        for existing in _engine.list_doctors():
            if existing.registry_code.upper() == reg_upper:
                raise ValueError(
                    f"Registro profissional '{clean_reg}' já está cadastrado.")
        try:
            with transaction.atomic():
                record = DoctorRecord.objects.create(
                    name=clean_name,
                    registry_code=clean_reg,
                    status="Disponível",
                    completed_count=0,
                    last_assigned_seq=0,
                )
                doctor = _engine.register_doctor(
                    doctor_id=record.id,
                    name=record.name,
                    registry_code=record.registry_code,
                )
                return doctor.to_dict()
        except IntegrityError as exc:
            raise ValueError(
                f"Registro profissional '{clean_reg}' já está cadastrado.") from exc
        except DatabaseError:
            _invalidate_cache()
            raise


def search_doctor(doctor_id: int) -> dict | None:
    with _lock:
        _ensure_hydrated()
        doctor = _engine.get_doctor(doctor_id)
        return doctor.to_dict() if doctor else None


def call_next_patient() -> dict:
    with _lock:
        _ensure_hydrated()
        patient, doctor = _engine.peek_next_call()
        next_seq = _engine.next_assignment_seq()
        started_at = datetime.now().strftime("%H:%M:%S")
        try:
            with transaction.atomic():
                att_record = AttendanceRecord.objects.create(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    status="Em atendimento",
                    started_at=started_at,
                )
                PatientRecord.objects.filter(
                    id=patient.id).update(status="Em atendimento")
                DoctorRecord.objects.filter(id=doctor.id).update(
                    status="Em atendimento",
                    last_assigned_seq=next_seq,
                )
                attendance = _engine.call_next(
                    attendance_id=att_record.id,
                    started_at=started_at,
                )
                return attendance.to_dict()
        except DatabaseError:
            _invalidate_cache()
            raise


def finish_attendance(attendance_id: int) -> dict:
    with _lock:
        _ensure_hydrated()
        finished_at = datetime.now().strftime("%H:%M:%S")
        try:
            with transaction.atomic():
                attendance = _engine.finish_attendance(
                    attendance_id, finished_at=finished_at)
                AttendanceRecord.objects.filter(id=attendance.id).update(
                    status="Concluído",
                    finished_at=finished_at,
                )
                PatientRecord.objects.filter(
                    id=attendance.patient.id).update(status="Concluído")
                DoctorRecord.objects.filter(id=attendance.doctor.id).update(
                    status="Disponível",
                    completed_count=attendance.doctor.completed_count,
                )
                return attendance.to_dict()
        except DatabaseError:
            _invalidate_cache()
            raise


def cancel_attendance(attendance_id: int) -> dict:
    with _lock:
        _ensure_hydrated()
        finished_at = datetime.now().strftime("%H:%M:%S")
        try:
            with transaction.atomic():
                attendance = _engine.cancel_attendance(
                    attendance_id, finished_at=finished_at)
                AttendanceRecord.objects.filter(id=attendance.id).update(
                    status="Cancelado",
                    finished_at=finished_at,
                )
                PatientRecord.objects.filter(
                    id=attendance.patient.id).update(status="Cancelado")
                DoctorRecord.objects.filter(
                    id=attendance.doctor.id).update(status="Disponível")
                return attendance.to_dict()
        except DatabaseError:
            _invalidate_cache()
            raise
