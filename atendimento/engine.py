from datetime import datetime
from .domain import Attendance, Doctor, Patient
from heap.min_heap import MinHeap
from rubro_negra.tree import RedBlackTree
from tabela_hash.hash_table import HashTable

VALID_PATIENT_STATUSES = ("Aguardando", "Em atendimento", "Concluído", "Cancelado")
VALID_DOCTOR_STATUSES = ("Disponível", "Em atendimento")
VALID_ATTENDANCE_STATUSES = ("Em atendimento", "Concluído", "Cancelado")


def parse_arrival_minutes(arrival_time: str) -> int:
    text = str(arrival_time).strip()
    parts = text.split(":")
    if len(parts) != 2 or not (parts[0].isdigit() and parts[1].isdigit()):
        raise ValueError("Horário inválido. Use o formato HH:MM.")
    hours, minutes = int(parts[0]), int(parts[1])
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError("Horário fora do intervalo válido (00:00 a 23:59).")
    return hours * 60 + minutes


def format_minutes_hhmm(total_minutes: int) -> str:
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _is_valid_priority(priority) -> bool:
    return isinstance(priority, int) and not isinstance(priority, bool) and (1 <= priority <= 5)


class SigaeEngine:
    """Núcleo em memória do SIGAE: mantém os índices sincronizados sem dict/heapq."""

    def __init__(self):
        self.patient_hash = HashTable(initial_capacity=11)
        self.doctor_hash = HashTable(initial_capacity=11)
        self.attendance_hash = HashTable(initial_capacity=11)

        self.rb_tree = RedBlackTree()
        self.patient_heap = MinHeap(key_fn=lambda p: (p.priority, p.arrival_minutes, p.id))
        self.doctor_heap = MinHeap(key_fn=lambda d: (d.completed_count, d.last_assigned_seq, d.id))

        self._active_attendances: list[Attendance] = []
        self._history: list[Attendance] = []
        self._assignment_seq: int = 0

    def clear(self) -> None:
        self.patient_hash.clear()
        self.doctor_hash.clear()
        self.attendance_hash.clear()
        self.rb_tree.clear()
        self.patient_heap.clear()
        self.doctor_heap.clear()
        self._active_attendances.clear()
        self._history.clear()
        self._assignment_seq = 0

    def hydrate_doctor(
        self,
        doctor_id: int,
        name: str,
        registry_code: str,
        status: str,
        completed_count: int,
        last_assigned_seq: int,
    ) -> Doctor:
        if status not in VALID_DOCTOR_STATUSES:
            raise ValueError(f"Situação de médico inválida: {status}")

        doctor = Doctor(
            doctor_id=doctor_id,
            name=str(name).strip(),
            registry_code=str(registry_code).strip(),
            status=status,
            completed_count=completed_count,
            last_assigned_seq=last_assigned_seq,
        )
        self.doctor_hash.put(doctor.id, doctor)
        if doctor.status == "Disponível":
            self.doctor_heap.insert(doctor)
        if last_assigned_seq > self._assignment_seq:
            self._assignment_seq = last_assigned_seq
        return doctor

    def hydrate_patient(
        self,
        patient_id: int,
        name: str,
        arrival_time: str,
        arrival_minutes: int,
        priority: int,
        status: str,
    ) -> Patient:
        if status not in VALID_PATIENT_STATUSES:
            raise ValueError(f"Situação de paciente inválida: {status}")
        if not _is_valid_priority(priority):
            raise ValueError("Classificação de risco deve estar entre 1 e 5.")

        patient = Patient(
            patient_id=patient_id,
            name=str(name).strip(),
            arrival_time=format_minutes_hhmm(arrival_minutes) if arrival_time else arrival_time,
            arrival_minutes=arrival_minutes,
            priority=priority,
            status=status,
        )
        self.patient_hash.put(patient.id, patient)
        if patient.status == "Aguardando":
            self.rb_tree.insert(patient)
            self.patient_heap.insert(patient)
        return patient

    def hydrate_attendance(
        self,
        attendance_id: int,
        patient_id: int,
        doctor_id: int,
        status: str,
        started_at: str,
        finished_at: str | None,
    ) -> Attendance:
        if status not in VALID_ATTENDANCE_STATUSES:
            raise ValueError(f"Situação de atendimento inválida: {status}")

        patient = self.patient_hash.get(patient_id)
        doctor = self.doctor_hash.get(doctor_id)
        if patient is None or doctor is None:
            raise ValueError("Inconsistência ao hidratar atendimento: paciente ou médico ausente.")

        attendance = Attendance(
            attendance_id=attendance_id,
            patient=patient,
            doctor=doctor,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
        )
        self.attendance_hash.put(attendance.id, attendance)
        if attendance.status == "Em atendimento":
            self._active_attendances.append(attendance)
        else:
            self._history.append(attendance)
        return attendance

    # ------------------------------------------------------------------
    # Operações de Pacientes
    # ------------------------------------------------------------------
    def register_patient(
        self,
        patient_id: int,
        name: str,
        arrival_time: str,
        priority: int,
    ) -> Patient:
        clean_name = str(name).strip()
        if len(clean_name) < 2 or len(clean_name) > 120:
            raise ValueError("Informe um nome válido (2 a 120 caracteres).")
        if not _is_valid_priority(priority):
            raise ValueError("Classificação de risco deve estar entre 1 e 5.")

        arrival_minutes = parse_arrival_minutes(arrival_time)
        normalized_time = format_minutes_hhmm(arrival_minutes)

        if self.patient_hash.contains(patient_id):
            raise ValueError(f"Paciente #{patient_id} já existe.")

        patient = Patient(
            patient_id=patient_id,
            name=clean_name,
            arrival_time=normalized_time,
            arrival_minutes=arrival_minutes,
            priority=priority,
            status="Aguardando",
        )

        # Inserção sincronizada com rollback atômico
        inserted_hash = False
        inserted_rb = False
        try:
            self.patient_hash.put(patient.id, patient)
            inserted_hash = True

            self.rb_tree.insert(patient)
            inserted_rb = True

            self.patient_heap.insert(patient)
            return patient
        except Exception:
            if inserted_rb:
                self.rb_tree.remove(patient)
            if inserted_hash:
                self.patient_hash.remove(patient.id)
            raise

    def get_patient(self, patient_id: int) -> Patient | None:
        return self.patient_hash.get(patient_id)

    def search_waiting_by_arrival(self, arrival_time: str, patient_id: int) -> Patient | None:
        arrival_minutes = parse_arrival_minutes(arrival_time)
        return self.rb_tree.search(arrival_minutes, patient_id)

    def reclassify_patient(self, patient_id: int, new_priority: int) -> Patient:
        if not _is_valid_priority(new_priority):
            raise ValueError("Nova classificação de risco deve estar entre 1 e 5.")

        patient = self.patient_hash.get(patient_id)
        if patient is None:
            raise ValueError(f"Paciente #{patient_id} não encontrado.")
        if patient.status != "Aguardando":
            raise ValueError("Só é possível reclassificar pacientes com situação 'Aguardando'.")

        old_priority = patient.priority
        try:
            patient.priority = new_priority
            self.patient_heap.update_item(patient)
            return patient
        except Exception:
            patient.priority = old_priority
            raise

    def cancel_waiting_patient(self, patient_id: int) -> Patient:
        patient = self.patient_hash.get(patient_id)
        if patient is None:
            raise ValueError(f"Paciente #{patient_id} não encontrado.")
        if patient.status != "Aguardando":
            raise ValueError("Paciente não está na fila de espera.")

        removed_heap = False
        try:
            if not self.patient_heap.remove(patient):
                raise RuntimeError("Falha ao remover paciente do Heap.")
            removed_heap = True

            if not self.rb_tree.remove(patient):
                raise RuntimeError("Falha ao remover paciente da Árvore Rubro-Negra.")

            patient.status = "Cancelado"
            return patient
        except Exception:
            if removed_heap:
                self.patient_heap.insert(patient)
            raise

    def list_waiting_chronological(self) -> list[Patient]:
        return self.rb_tree.inorder()

    # ------------------------------------------------------------------
    # Operações de Médicos
    # ------------------------------------------------------------------
    def register_doctor(self, doctor_id: int, name: str, registry_code: str) -> Doctor:
        clean_name = str(name).strip()
        clean_reg = str(registry_code).strip()
        if len(clean_name) < 2 or len(clean_name) > 120:
            raise ValueError("Informe um nome de médico válido (2 a 120 caracteres).")
        if len(clean_reg) < 3 or len(clean_reg) > 40:
            raise ValueError("Informe um registro profissional fictício válido.")

        if self.doctor_hash.contains(doctor_id):
            raise ValueError(f"Médico #{doctor_id} já existe.")

        reg_normalized = clean_reg.upper()
        for existing in self.doctor_hash.values():
            if existing.registry_code.upper() == reg_normalized:
                raise ValueError(f"Registro profissional '{clean_reg}' já está cadastrado.")

        doctor = Doctor(doctor_id=doctor_id, name=clean_name, registry_code=clean_reg)

        inserted_hash = False
        try:
            self.doctor_hash.put(doctor.id, doctor)
            inserted_hash = True

            self.doctor_heap.insert(doctor)
            return doctor
        except Exception:
            if inserted_hash:
                self.doctor_hash.remove(doctor.id)
            raise

    def get_doctor(self, doctor_id: int) -> Doctor | None:
        return self.doctor_hash.get(doctor_id)

    def list_doctors(self) -> list[Doctor]:
        doctors = self.doctor_hash.values()
        doctors.sort(key=lambda d: d.id)
        return doctors

    # ------------------------------------------------------------------
    # Chamada, Atendimento, Conclusão e Cancelamento de Atendimento
    # ------------------------------------------------------------------
    def peek_next_call(self) -> tuple[Patient, Doctor]:
        """Valida pré-condições sem alterar nenhuma estrutura."""
        patient = self.patient_heap.peek()
        if patient is None:
            raise ValueError("Não há pacientes aguardando na fila.")

        doctor = self.doctor_heap.peek()
        if doctor is None:
            raise ValueError("Nenhum médico disponível no momento. O paciente permanece na fila.")

        return patient, doctor

    def next_assignment_seq(self) -> int:
        return self._assignment_seq + 1

    def call_next(self, attendance_id: int, started_at: str | None = None) -> Attendance:
        if self.attendance_hash.contains(attendance_id):
            raise ValueError(f"Atendimento #{attendance_id} já existe.")

        patient, doctor = self.peek_next_call()

        removed_patient_heap = False
        removed_rb = False
        removed_doctor_heap = False
        inserted_attendance_hash = False
        prev_seq = doctor.last_assigned_seq
        prev_engine_seq = self._assignment_seq

        try:
            extracted_patient = self.patient_heap.extract_min()
            if extracted_patient is not patient:
                raise RuntimeError("Inconsistência ao extrair paciente do Heap.")
            removed_patient_heap = True

            if not self.rb_tree.remove(patient):
                raise RuntimeError("Falha ao remover paciente da Árvore Rubro-Negra.")
            removed_rb = True

            extracted_doctor = self.doctor_heap.extract_min()
            if extracted_doctor is not doctor:
                raise RuntimeError("Inconsistência ao extrair médico do Heap.")
            removed_doctor_heap = True

            self._assignment_seq += 1
            doctor.last_assigned_seq = self._assignment_seq
            doctor.status = "Em atendimento"
            patient.status = "Em atendimento"

            attendance = Attendance(
                attendance_id=attendance_id,
                patient=patient,
                doctor=doctor,
                status="Em atendimento",
                started_at=started_at or datetime.now().strftime("%H:%M:%S"),
            )
            self.attendance_hash.put(attendance.id, attendance)
            inserted_attendance_hash = True
            self._active_attendances.append(attendance)
            return attendance
        except Exception:
            if inserted_attendance_hash:
                self.attendance_hash.remove(attendance_id)
            self._assignment_seq = prev_engine_seq
            if removed_doctor_heap:
                doctor.last_assigned_seq = prev_seq
                doctor.status = "Disponível"
                self.doctor_heap.insert(doctor)
            if removed_rb:
                self.rb_tree.insert(patient)
            if removed_patient_heap:
                patient.status = "Aguardando"
                self.patient_heap.insert(patient)
            raise

    def finish_attendance(self, attendance_id: int, finished_at: str | None = None) -> Attendance:
        attendance = self.attendance_hash.get(attendance_id)
        if attendance is None:
            raise ValueError(f"Atendimento #{attendance_id} não encontrado.")
        if attendance.status != "Em atendimento":
            raise ValueError("Este atendimento já foi encerrado.")

        doctor = attendance.doctor
        patient = attendance.patient
        prev_completed = doctor.completed_count
        prev_doc_status = doctor.status
        prev_pat_status = patient.status
        prev_att_status = attendance.status
        prev_finished_at = attendance.finished_at
        inserted_heap = False

        try:
            # Incrementa contador e devolve o médico ao Heap de disponíveis
            doctor.completed_count += 1
            doctor.status = "Disponível"
            self.doctor_heap.insert(doctor)
            inserted_heap = True

            attendance.status = "Concluído"
            attendance.finished_at = finished_at or datetime.now().strftime("%H:%M:%S")
            patient.status = "Concluído"

            self._active_attendances.remove(attendance)
            self._history.append(attendance)
            return attendance
        except Exception:
            if inserted_heap:
                self.doctor_heap.remove(doctor)
            doctor.completed_count = prev_completed
            doctor.status = prev_doc_status
            patient.status = prev_pat_status
            attendance.status = prev_att_status
            attendance.finished_at = prev_finished_at
            raise

    def cancel_attendance(self, attendance_id: int, finished_at: str | None = None) -> Attendance:
        attendance = self.attendance_hash.get(attendance_id)
        if attendance is None:
            raise ValueError(f"Atendimento #{attendance_id} não encontrado.")
        if attendance.status != "Em atendimento":
            raise ValueError("Só é possível cancelar atendimentos em andamento.")

        doctor = attendance.doctor
        patient = attendance.patient
        prev_doc_status = doctor.status
        prev_pat_status = patient.status
        prev_att_status = attendance.status
        prev_finished_at = attendance.finished_at
        inserted_heap = False

        try:
            # Cancelamento anterior à conclusão NÃO aumenta completed_count
            doctor.status = "Disponível"
            self.doctor_heap.insert(doctor)
            inserted_heap = True

            attendance.status = "Cancelado"
            attendance.finished_at = finished_at or datetime.now().strftime("%H:%M:%S")
            patient.status = "Cancelado"

            self._active_attendances.remove(attendance)
            self._history.append(attendance)
            return attendance
        except Exception:
            if inserted_heap:
                self.doctor_heap.remove(doctor)
            doctor.status = prev_doc_status
            patient.status = prev_pat_status
            attendance.status = prev_att_status
            attendance.finished_at = prev_finished_at
            raise

    # ------------------------------------------------------------------
    # Validação de Consistência e Snapshot para a Interface Web
    # ------------------------------------------------------------------
    def validate_all(self) -> bool:
        self.patient_hash.validate()
        self.doctor_hash.validate()
        self.attendance_hash.validate()
        self.rb_tree.validate()
        self.patient_heap.validate()
        self.doctor_heap.validate()

        waiting_from_hash = sorted(
            p.id for p in self.patient_hash.values() if p.status == "Aguardando"
        )
        waiting_from_rb = sorted(p.id for p in self.rb_tree.inorder())
        waiting_from_heap = sorted(p.id for p in self.patient_heap.all_items())

        if waiting_from_hash != waiting_from_rb or waiting_from_hash != waiting_from_heap:
            raise AssertionError("Inconsistência entre os índices de pacientes aguardando.")

        available_from_hash = sorted(
            d.id for d in self.doctor_hash.values() if d.status == "Disponível"
        )
        available_from_heap = sorted(d.id for d in self.doctor_heap.all_items())

        if available_from_hash != available_from_heap:
            raise AssertionError("Inconsistência entre a Hash e o Heap de médicos disponíveis.")

        active_ids = sorted(a.id for a in self._active_attendances)
        hash_active_ids = sorted(
            a.id for a in self.attendance_hash.values() if a.status == "Em atendimento"
        )
        if active_ids != hash_active_ids:
            raise AssertionError("Inconsistência entre atendimentos ativos e a Hash de atendimentos.")

        busy_doctors = sorted(
            d.id for d in self.doctor_hash.values() if d.status == "Em atendimento"
        )
        active_att_doctors = sorted(a.doctor.id for a in self._active_attendances)
        if busy_doctors != active_att_doctors:
            raise AssertionError("Inconsistência entre médicos ocupados e atendimentos ativos.")

        busy_patients = sorted(
            p.id for p in self.patient_hash.values() if p.status == "Em atendimento"
        )
        active_att_patients = sorted(a.patient.id for a in self._active_attendances)
        if busy_patients != active_att_patients:
            raise AssertionError("Inconsistência entre pacientes em atendimento e atendimentos ativos.")

        return True

    def get_snapshot(self) -> dict:
        all_patients = self.patient_hash.values()
        all_doctors = self.list_doctors()

        # Fila ordenada por prioridade apenas para exibição (sem alterar o Heap)
        waiting_priority = sorted(
            self.patient_heap.all_items(),
            key=lambda p: (p.priority, p.arrival_minutes, p.id),
        )
        waiting_chronological = self.rb_tree.inorder()

        next_patient = self.patient_heap.peek()
        next_doctor = self.doctor_heap.peek()

        counts = {
            "aguardando": sum(1 for p in all_patients if p.status == "Aguardando"),
            "em_atendimento": sum(1 for p in all_patients if p.status == "Em atendimento"),
            "concluido": sum(1 for p in all_patients if p.status == "Concluído"),
            "cancelado": sum(1 for p in all_patients if p.status == "Cancelado"),
            "medicos_disponiveis": len(self.doctor_heap),
            "medicos_ocupados": sum(1 for d in all_doctors if d.status == "Em atendimento"),
        }

        return {
            "counts": counts,
            "next_patient": next_patient.to_dict() if next_patient else None,
            "next_doctor": next_doctor.to_dict() if next_doctor else None,
            "waiting_priority": [p.to_dict() for p in waiting_priority],
            "waiting_chronological": [p.to_dict() for p in waiting_chronological],
            "all_patients": [
                p.to_dict() for p in sorted(all_patients, key=lambda p: p.id, reverse=True)
            ],
            "doctors": [d.to_dict() for d in all_doctors],
            "active_attendances": [a.to_dict() for a in self._active_attendances],
            "history": [a.to_dict() for a in reversed(self._history)],
            "diagnostics": {
                "rb_tree": self.rb_tree.serialize(),
                "patient_heap": self.patient_heap.serialize(),
                "doctor_heap": self.doctor_heap.serialize(),
                "patient_hash": self.patient_hash.serialize(),
                "doctor_hash": self.doctor_hash.serialize(),
            },
        }
