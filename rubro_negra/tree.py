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
    def is_empty(self) -> bool:
        return self.root is self.NIL

    def _left_rotate(self, x: _RBNode) -> None:
        y = x.right
        x.right = y.left
        if y.left is not self.NIL:
            y.left.parent = x

        y.parent = x.parent
        if x.parent is self.NIL:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        y.left = x
        x.parent = y
        self.rotations += 1
    def _right_rotate(self, y: _RBNode) -> None:
        x = y.left
        y.left = x.right
        if x.right is not self.NIL:
            x.right.parent = y

        x.parent = y.parent
        if y.parent is self.NIL:
            self.root = x
        elif y is y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x

        x.right = y
        y.parent = x
        self.rotations += 1