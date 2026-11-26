from django.test import SimpleTestCase
from atendimento.domain import Doctor, Patient
from .min_heap import MinHeap

# Create your tests here.

class MinHeapTests(SimpleTestCase):
    def _make_patient_heap(self):
        return MinHeap(key_fn=lambda p: (p.priority, p.arrival_minutes, p.id))

    def _make_doctor_heap(self):
        return MinHeap(key_fn=lambda d: (d.completed_count, d.last_assigned_seq, d.id))

    def test_patient_priority_and_tiebreakers(self):
        heap = self._make_patient_heap()

        p_low = Patient(1, "Pouco Urgente", "08:00", 480, 4)
        p_urg_late = Patient(2, "Urgente Tarde", "08:10", 490, 2)
        p_urg_early_id5 = Patient(5, "Urgente Cedo ID5", "08:05", 485, 2)
        p_urg_early_id3 = Patient(3, "Urgente Cedo ID3", "08:05", 485, 2)
        p_emerg = Patient(4, "Emergência", "08:20", 500, 1)

        for p in (p_low, p_urg_late, p_urg_early_id5, p_urg_early_id3, p_emerg):
            heap.insert(p)
            self.assertTrue(heap.validate())

        extracted_ids = []
        while not heap.is_empty():
            extracted_ids.append(heap.extract_min().id)
            self.assertTrue(heap.validate())

        self.assertEqual(extracted_ids, [4, 3, 5, 2, 1])

    def test_reclassify_patient_up_and_down(self):
        heap = self._make_patient_heap()

        p1 = Patient(1, "P1", "08:00", 480, 3)
        p2 = Patient(2, "P2", "08:05", 485, 2)
        p3 = Patient(3, "P3", "08:10", 490, 4)

        for p in (p1, p2, p3):
            heap.insert(p)

        self.assertIs(heap.peek(), p2)

        p3.priority = 1
        heap.update_item(p3)
        self.assertTrue(heap.validate())
        self.assertIs(heap.peek(), p3)

        p3.priority = 5
        heap.update_item(p3)
        self.assertTrue(heap.validate())
        self.assertIs(heap.peek(), p2)

    def test_remove_arbitrary_item_from_middle(self):
        heap = self._make_patient_heap()
        patients = [Patient(i, f"Pac {i}", f"08:{i:02d}", 480 + i, (i % 5) + 1) for i in range(1, 10)]

        for p in patients:
            heap.insert(p)

        target = patients[4]
        self.assertTrue(heap.remove(target))
        self.assertEqual(target.heap_index, -1)
        self.assertEqual(len(heap), 8)
        self.assertTrue(heap.validate())

    def test_doctor_balancing_and_deterministic_tiebreak(self):
        heap = self._make_doctor_heap()

        doc_a = Doctor(1, "Dra. Ana", "CRM-001")
        doc_b = Doctor(2, "Dr. Bruno", "CRM-002")
        doc_c = Doctor(3, "Dra. Carla", "CRM-003")

        for d in (doc_c, doc_b, doc_a):
            heap.insert(d)

        first = heap.extract_min()
        self.assertIs(first, doc_a)
        first.completed_count += 1
        first.last_assigned_seq = 1
        heap.insert(first)
        self.assertTrue(heap.validate())

        second = heap.extract_min()
        self.assertIs(second, doc_b)
        second.completed_count += 1
        second.last_assigned_seq = 2
        heap.insert(second)

        third = heap.extract_min()
        self.assertIs(third, doc_c)
        third.completed_count += 1
        third.last_assigned_seq = 3
        heap.insert(third)
        self.assertTrue(heap.validate())

        self.assertIs(heap.peek(), doc_a)