RED = 0
BLACK = 1

class _RBNode:
    __slots__ = ("key", "patient", "color", "left", "right", "parent")

    def __init__(self, key: tuple[int, int] | None, patient=None, color: int = RED, nil=None):
        self.key = key
        self.patient = patient
        self.color = color
        self.left = nil
        self.right = nil
        self.parent = nil

class RedBlackTree:
    
    def __init__(self):
        self.NIL = _RBNode(key=None, patient=None, color=BLACK)
        self.NIL.left = self.NIL
        self.NIL.right = self.NIL
        self.NIL.parent = self.NIL

        self.root = self.NIL
        self._size = 0
        self.rotations = 0