from django.shortcuts import render
from django.db import DatabaseError
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
import json
from . import services

# Create your views here.


def _parse_json_body(request) -> dict:
    try:
        raw = request.body.decode("utf-8") if request.body else "{}"
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Corpo da requisição inválido (esperado JSON).") from exc
    if not isinstance(data, dict):
        raise ValueError("O payload JSON deve ser um objeto.")
    return data


def _parse_strict_int(value, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(
            f"Campo '{field_name}' deve ser um número inteiro positivo.")
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        if parsed > 0:
            return parsed
    raise ValueError(
        f"Campo '{field_name}' deve ser um número inteiro positivo.")


def _error_response(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": message}, status=status)


@ensure_csrf_cookie
@require_GET
def dashboard(request):
    return render(request, "atendimento/dashboard.html")


@require_GET
def api_state(request):
    try:
        return JsonResponse({"ok": True, "snapshot": services.get_snapshot()})
    except DatabaseError:
        return _error_response("Erro interno ao acessar o banco de dados.", status=500)


@require_POST
def api_validate(request):
    try:
        valid = services.validate_all()
        return JsonResponse(
            {
                "ok": True,
                "valid": valid,
                "message": "Validação concluída: Rubro-Negra, Heaps, Tabelas Hash e vínculos consistentes.",
                "snapshot": services.get_snapshot(),
            }
        )
    except (AssertionError, ValueError) as exc:
        return _error_response(str(exc), status=500)
    except DatabaseError:
        return _error_response("Erro interno ao acessar o banco de dados.", status=500)


@require_POST
def api_register_patient(request):
    try:
        data = _parse_json_body(request)
        name = data.get("name", "")
        arrival_time = data.get("arrival_time", "")
        priority = _parse_strict_int(data.get("priority"), "priority")
        patient = services.register_patient(
            name=name,
            arrival_time=arrival_time,
            priority=priority,
        )
        return JsonResponse(
            {
                "ok": True,
                "patient": patient,
                "message": f"Paciente #{patient['id']} ({patient['name']}) registrado na fila.",
                "snapshot": services.get_snapshot(),
            },
            status=201,
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao persistir paciente no banco.", status=500)


@require_GET
def api_search_patient(request, patient_id: int):
    try:
        patient = services.search_patient(patient_id)
        if patient is None:
            return _error_response(f"Paciente #{patient_id} não encontrado.", status=404)
        return JsonResponse({"ok": True, "patient": patient})
    except DatabaseError:
        return _error_response("Erro interno ao acessar o banco de dados.", status=500)


@require_GET
def api_search_by_arrival(request):
    try:
        arrival_time = request.GET.get("arrival_time", "")
        patient_id = _parse_strict_int(
            request.GET.get("patient_id"), "patient_id")
        patient = services.search_waiting_by_arrival(arrival_time, patient_id)
        if patient is None:
            return _error_response(
                f"Nenhum paciente aguardando com chegada {arrival_time} e ID #{patient_id}.",
                status=404,
            )
        return JsonResponse({"ok": True, "patient": patient})
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao acessar o banco de dados.", status=500)


@require_POST
def api_reclassify_patient(request, patient_id: int):
    try:
        data = _parse_json_body(request)
        new_priority = _parse_strict_int(data.get("priority"), "priority")
        patient = services.reclassify_patient(patient_id, new_priority)
        return JsonResponse(
            {
                "ok": True,
                "patient": patient,
                "message": f"Paciente #{patient['id']} reclassificado para P{patient['priority']} ({patient['priority_label']}).",
                "snapshot": services.get_snapshot(),
            }
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao atualizar classificação no banco.", status=500)


@require_POST
def api_cancel_waiting_patient(request, patient_id: int):
    try:
        patient = services.cancel_waiting_patient(patient_id)
        return JsonResponse(
            {
                "ok": True,
                "patient": patient,
                "message": f"Cadastro do paciente #{patient['id']} cancelado e removido da fila.",
                "snapshot": services.get_snapshot(),
            }
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao cancelar paciente no banco.", status=500)


@require_POST
def api_register_doctor(request):
    try:
        data = _parse_json_body(request)
        name = data.get("name", "")
        registry_code = data.get("registry_code", "")
        doctor = services.register_doctor(
            name=name, registry_code=registry_code)
        return JsonResponse(
            {
                "ok": True,
                "doctor": doctor,
                "message": f"Médico #{doctor['id']} ({doctor['name']} · {doctor['registry_code']}) cadastrado.",
                "snapshot": services.get_snapshot(),
            },
            status=201,
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao persistir médico no banco.", status=500)


@require_GET
def api_search_doctor(request, doctor_id: int):
    try:
        doctor = services.search_doctor(doctor_id)
        if doctor is None:
            return _error_response(f"Médico #{doctor_id} não encontrado.", status=404)
        return JsonResponse({"ok": True, "doctor": doctor})
    except DatabaseError:
        return _error_response("Erro interno ao acessar o banco de dados.", status=500)


@require_POST
def api_call_next(request):
    try:
        attendance = services.call_next_patient()
        return JsonResponse(
            {
                "ok": True,
                "attendance": attendance,
                "message": (
                    f"Atendimento #{attendance['id']} iniciado: "
                    f"Paciente #{attendance['patient']['id']} ({attendance['patient']['name']}) "
                    f"vinculado ao(à) {attendance['doctor']['name']}."
                ),
                "snapshot": services.get_snapshot(),
            },
            status=201,
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao registrar chamada no banco.", status=500)


@require_POST
def api_finish_attendance(request, attendance_id: int):
    try:
        attendance = services.finish_attendance(attendance_id)
        return JsonResponse(
            {
                "ok": True,
                "attendance": attendance,
                "message": (
                    f"Atendimento #{attendance['id']} concluído. "
                    f"{attendance['doctor']['name']} disponível ({attendance['doctor']['completed_count']} concluídos)."
                ),
                "snapshot": services.get_snapshot(),
            }
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao concluir atendimento no banco.", status=500)


@require_POST
def api_cancel_attendance(request, attendance_id: int):
    try:
        attendance = services.cancel_attendance(attendance_id)
        return JsonResponse(
            {
                "ok": True,
                "attendance": attendance,
                "message": (
                    f"Atendimento #{attendance['id']} cancelado. "
                    f"{attendance['doctor']['name']} liberado sem alterar contador."
                ),
                "snapshot": services.get_snapshot(),
            }
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except DatabaseError:
        return _error_response("Erro interno ao cancelar atendimento no banco.", status=500)
