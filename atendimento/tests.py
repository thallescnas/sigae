from django.test import SimpleTestCase
from .engine import SigaeEngine


class SigaeEngineTests(SimpleTestCase):
    def setUp(self):
        self.engine = SigaeEngine()

    def test_three_doctors_balanced_distribution_and_tiebreak(self):
        doc_a = self.engine.register_doctor(1, "Dra. Ana", "CRM-1001")
        doc_b = self.engine.register_doctor(2, "Dr. Bruno", "CRM-1002")
        doc_c = self.engine.register_doctor(3, "Dra. Carla", "CRM-1003")

        for i in range(1, 6):
            self.engine.register_patient(i, f"Paciente {i}", f"08:{i:02d}", 3)

        att1 = self.engine.call_next(1, started_at="08:10:00")
        att2 = self.engine.call_next(2, started_at="08:11:00")
        att3 = self.engine.call_next(3, started_at="08:12:00")
        self.assertEqual([att1.doctor.id, att2.doctor.id, att3.doctor.id], [1, 2, 3])
        self.assertTrue(self.engine.validate_all())

        with self.assertRaises(ValueError):
            self.engine.call_next(99)
        self.assertEqual(len(self.engine.patient_heap), 2)
        self.assertTrue(self.engine.validate_all())

        self.engine.finish_attendance(att2.id, finished_at="08:20:00")
        self.engine.finish_attendance(att3.id, finished_at="08:21:00")
        self.assertEqual(doc_b.completed_count, 1)
        self.assertEqual(doc_c.completed_count, 1)

        att4 = self.engine.call_next(4, started_at="08:22:00")
        self.assertIs(att4.doctor, doc_b)
        self.assertTrue(self.engine.validate_all())

        self.engine.finish_attendance(att4.id, finished_at="08:25:00")
        self.engine.finish_attendance(att1.id, finished_at="08:26:00")

        att5 = self.engine.call_next(5, started_at="08:27:00")
        self.assertIs(att5.doctor, doc_a)
        self.assertTrue(self.engine.validate_all())

    def test_priority_prevalence_reclassification_and_chronological_order(self):
        self.engine.register_doctor(1, "Dr. Plantonista", "CRM-2001")

        p1 = self.engine.register_patient(1, "Chegou Cedo Pouco Urgente", "8:05", 4)
        p2 = self.engine.register_patient(2, "Chegou Tarde Emergência", "08:30", 1)
        p3 = self.engine.register_patient(3, "Chegou Médio Urgente", "08:15", 3)

        self.assertEqual(p1.arrival_time, "08:05")
        self.assertIs(self.engine.search_waiting_by_arrival("08:05", 1), p1)

        self.assertEqual(
            [p.id for p in self.engine.list_waiting_chronological()],
            [1, 3, 2],
        )

        self.engine.reclassify_patient(1, 1)
        self.assertEqual(len(self.engine.patient_heap), 3)
        self.assertTrue(self.engine.validate_all())

        att = self.engine.call_next(1, started_at="08:31:00")
        self.assertIs(att.patient, p1)
        self.assertTrue(self.engine.validate_all())

    def test_cancel_waiting_and_cancel_attendance_preserve_counts_and_invariants(self):
        doc = self.engine.register_doctor(1, "Dra. Sofia", "CRM-3001")
        p1 = self.engine.register_patient(1, "Paciente Fila", "09:00", 2)
        p2 = self.engine.register_patient(2, "Paciente Consultório", "09:05", 1)

        self.engine.cancel_waiting_patient(p1.id)
        self.assertEqual(p1.status, "Cancelado")
        self.assertEqual(len(self.engine.patient_heap), 1)
        self.assertEqual(len(self.engine.rb_tree), 1)
        self.assertTrue(self.engine.validate_all())

        att = self.engine.call_next(10, started_at="09:10:00")
        self.assertIs(att.patient, p2)
        self.engine.cancel_attendance(att.id, finished_at="09:12:00")

        self.assertEqual(doc.completed_count, 0)
        self.assertEqual(doc.status, "Disponível")
        self.assertEqual(p2.status, "Cancelado")
        self.assertEqual(att.status, "Cancelado")
        self.assertTrue(self.engine.validate_all())

    def test_validation_guards_bool_priority_and_duplicate_crm(self):
        self.engine.register_doctor(1, "Dr. A", "CRM-9999")
        with self.assertRaises(ValueError):
            self.engine.register_doctor(2, "Dr. B", "crm-9999")

        with self.assertRaises(ValueError):
            self.engine.register_patient(1, "Paciente Bool", "10:00", True)
