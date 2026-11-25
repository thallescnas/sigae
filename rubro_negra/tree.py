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

    def _left_rotate(self, x: _RBNode):
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
    def _right_rotate(self, y: _RBNode):
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

    def insert(self, patient):
        if patient.rb_node is not None:
            raise ValueError(f"O paciente {patient.id} já se encontra na arvore rubro negra!")
        key = (patient.arrival_minutes, patient.id)
        new_node = _RBNode(key=key, patient=patient, color=RED, nil=self.NIL)

        parent = self.NIL
        curr = self.root
        while curr is not self.NIL:
            parent = curr
            if key < curr.key:
                curr = curr.left
            elif key > curr.key:
                curr = curr.right
            else: raise ValueError(f"Key duplicada na rubro negra: {key}")
        new_node.parent = parent
        if parent is self.NIL:
            self.root = new_node
        elif key < parent.key:
            parent.left = new_node
        else:
            parent.right = new_node

        patient.rb_node = new_node
        self._size += 1
        self._fix_insert(new_node)

    def _fix_insert(self, z: _RBNode):
        while z.parent.color == RED:
            grandparent = z.parent.parent
            if z.parent is grandparent.left:
                uncle = grandparent.right
                if uncle.color == RED:
                    z.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    z = grandparent
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = BLACK
                    grandparent.color = RED
                    self._right_rotate(grandparent)
            else:
                uncle = grandparent.left
                if uncle.color == RED:
                    z.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    z = grandparent
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = BLACK
                    grandparent.color = RED
                    self._left_rotate(grandparent)
        self.root.color = BLACK
    def search(self, arrival_minutes: int, patient_id: int):
        target = (arrival_minutes, patient_id)
        curr = self.root
        while curr is not self.NIL:
            if target == curr.key:
                return curr.patient
            if target < curr.key:
                curr = curr.left
            else:
                curr = curr.right
        return None

    def _transplant(self, u: _RBNode, v: _RBNode) -> None:
        if u.parent is self.NIL:
            self.root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent