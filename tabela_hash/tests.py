from django.test import SimpleTestCase
from atendimento.domain import Doctor, Patient
from .hash_table import HashTable

# Create your tests here.

class HashTableTests(SimpleTestCase):
    def test_put_get_and_remove_patient(self):
        table = HashTable(initial_capacity=11)
        p1 = Patient(1001, "Ana Ribeiro", "08:00", 480, 3)

        table.put(p1.id, p1)
        self.assertEqual(len(table), 1)
        self.assertTrue(table.contains(1001))
        self.assertIs(table.get(1001), p1)
        self.assertTrue(table.validate())

        removed = table.remove(1001)
        self.assertIs(removed, p1)
        self.assertEqual(len(table), 0)
        self.assertIsNone(table.get(1001))
        self.assertTrue(table.validate())

    def test_rejects_duplicate_key(self):
        table = HashTable(initial_capacity=11)
        p1 = Patient(1000, "Ana", "08:00", 480, 2)
        p2 = Patient(1000, "Outra Ana", "08:05", 485, 1)

        table.put(p1.id, p1)
        with self.assertRaises(ValueError):
            table.put(p2.id, p2)

    def test_collision_chaining_and_middle_removal(self):
        table = HashTable(initial_capacity=11)
        p1 = Patient(1000, "Ana", "08:00", 480, 4)
        p2 = Patient(1011, "Bruno", "08:05", 485, 2)
        p3 = Patient(1022, "Carlos", "08:10", 490, 5)

        table.put(p1.id, p1)
        table.put(p2.id, p2)
        table.put(p3.id, p3)

        self.assertEqual(table.collisions, 2)
        self.assertIs(table.get(1000), p1)
        self.assertIs(table.get(1011), p2)
        self.assertIs(table.get(1022), p3)
        self.assertTrue(table.validate())

        self.assertIs(table.remove(1011), p2)
        self.assertIsNone(table.get(1011))
        self.assertIs(table.get(1000), p1)
        self.assertIs(table.get(1022), p3)
        self.assertEqual(len(table), 2)
        self.assertTrue(table.validate())

    def test_automatic_rehash_when_load_factor_exceeded(self):
        table = HashTable(initial_capacity=5, max_load_factor=0.75)
        doctors = [Doctor(i, f"Dr. {i}", f"CRM-{i:04d}") for i in range(1, 20)]

        for doc in doctors:
            table.put(doc.id, doc)

        self.assertGreater(table.rehash_count, 0)
        self.assertGreater(table.capacity, 5)
        self.assertLessEqual(table.load_factor, 0.75)
        self.assertEqual(len(table), len(doctors))
        self.assertTrue(table.validate())

        for doc in doctors:
            self.assertIs(table.get(doc.id), doc)
