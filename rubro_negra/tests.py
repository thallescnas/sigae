from django.test import SimpleTestCase
from atendimento.domain import Patient
from .tree import BLACK, RedBlackTree

# Create your tests here.


class RedBlackTreeTests(SimpleTestCase):
    def test_insert_ascending_triggers_rotations_and_keeps_invariants(self):
        tree = RedBlackTree()
        patients = [
            Patient(i, f"Paciente {i}", f"08:{i:02d}", 480 + i, 3)
            for i in range(1, 25)
        ]

        for p in patients:
            tree.insert(p)
            self.assertEqual(tree.root.color, BLACK)
            self.assertTrue(tree.validate())

        self.assertGreater(tree.rotations, 0)
        self.assertEqual([p.id for p in tree.inorder()], [p.id for p in patients])

    def test_insert_descending_and_same_arrival_time_tiebreak_by_id(self):
        tree = RedBlackTree()
        # Mesmo horário (08:15 = 495 min) com IDs fora de ordem
        p_id30 = Patient(30, "Carla", "08:15", 495, 2)
        p_id10 = Patient(10, "Ana", "08:15", 495, 5)
        p_id20 = Patient(20, "Bruno", "08:15", 495, 1)
        p_early = Patient(99, "Mais Cedo", "08:00", 480, 4)

        for p in (p_id30, p_id10, p_id20, p_early):
            tree.insert(p)
            self.assertTrue(tree.validate())

        ordered_ids = [p.id for p in tree.inorder()]
        self.assertEqual(ordered_ids, [99, 10, 20, 30])

        # Busca exata por (horário em minutos, ID)
        self.assertIs(tree.search(495, 20), p_id20)
        self.assertIsNone(tree.search(495, 999))

    def test_remove_root_leaves_and_internal_nodes_preserves_rb_properties(self):
        tree = RedBlackTree()
        # Ordem mista para exercitar casos 1, 2, 3 e 4 do delete fix-up
        keys = [50, 20, 80, 10, 30, 70, 90, 5, 15, 25, 35, 65, 75, 85, 95, 1, 40, 60]
        patients = [
            Patient(k, f"Pac {k}", f"{k // 60:02d}:{k % 60:02d}", k, 3)
            for k in keys
        ]

        for p in patients:
            tree.insert(p)
            self.assertTrue(tree.validate())

        # Remove a raiz atual primeiro e depois vários nós em ordens diferentes
        removal_order = [tree.root.patient] + [p for p in patients if p is not tree.root.patient]

        for p in removal_order:
            self.assertTrue(tree.remove(p))
            self.assertIsNone(p.rb_node)
            self.assertTrue(tree.validate())

        self.assertTrue(tree.is_empty())
        self.assertEqual(len(tree), 0)
        self.assertEqual(tree.inorder(), [])

    def test_rejects_duplicate_insertion(self):
        tree = RedBlackTree()
        p1 = Patient(1, "Ana", "08:00", 480, 3)
        tree.insert(p1)

        with self.assertRaises(ValueError):
            tree.insert(p1)