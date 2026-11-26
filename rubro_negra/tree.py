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

    def __len__(self) -> int:
        return self._size

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

    def _minimum(self, node: _RBNode) -> _RBNode:
        while node.left is not self.NIL:
            node = node.left
        return node

    def remove(self, patient) -> bool:
        z = patient.rb_node
        if z is None or z is self.NIL:
            return False

        y = z
        y_original_color = y.color

        if z.left is self.NIL:
            x = z.right
            self._transplant(z, z.right)
        elif z.right is self.NIL:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent is z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y

            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

        patient.rb_node = None
        z.left = None
        z.right = None
        z.parent = None
        self._size -= 1

        if y_original_color == BLACK:
            self._fix_delete(x)

        self.NIL.parent = self.NIL
        self.NIL.color = BLACK
        if self.root is not self.NIL:
            self.root.color = BLACK

        return True

    def _fix_delete(self, x: _RBNode) -> None:
        while x is not self.root and x.color == BLACK:
            if x is x.parent.left:
                w = x.parent.right
                if w.color == RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._left_rotate(x.parent)
                    w = x.parent.right

                if w.left.color == BLACK and w.right.color == BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.right.color == BLACK:
                        w.left.color = BLACK
                        w.color = RED
                        self._right_rotate(w)
                        w = x.parent.right
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.right.color = BLACK
                    self._left_rotate(x.parent)
                    x = self.root
            else:
                w = x.parent.left
                if w.color == RED:
                    # Caso 1
                    w.color = BLACK
                    x.parent.color = RED
                    self._right_rotate(x.parent)
                    w = x.parent.left

                if w.right.color == BLACK and w.left.color == BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.left.color == BLACK:
                        w.right.color = BLACK
                        w.color = RED
                        self._left_rotate(w)
                        w = x.parent.left
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.left.color = BLACK
                    self._right_rotate(x.parent)
                    x = self.root

        x.color = BLACK

    def inorder(self) -> list:
        result = []

        def _walk(node: _RBNode) -> None:
            if node is self.NIL:
                return
            _walk(node.left)
            result.append(node.patient)
            _walk(node.right)

        _walk(self.root)
        return result

    def height(self) -> int:
        def _h(node: _RBNode) -> int:
            if node is self.NIL:
                return 0
            return 1 + max(_h(node.left), _h(node.right))

        return _h(self.root)

    def clear(self) -> None:
        for patient in self.inorder():
            patient.rb_node = None
        self.root = self.NIL
        self._size = 0
        self.rotations = 0

    def validate(self) -> bool:
        if self.NIL.color != BLACK:
            raise AssertionError("Propriedade 3 violada: folha NIL não é negra.")

        if self.root is self.NIL:
            if self._size != 0:
                raise AssertionError("Tree vazia com _size != 0.")
            return True

        if self.root.color != BLACK:
            raise AssertionError("Propriedade 2 violada: a raiz não é negra.")

        if self.root.parent is not self.NIL:
            raise AssertionError("Raiz com referência de pai inválida.")

        visited = 0

        def _check(node: _RBNode, min_key, max_key) -> int:
            nonlocal visited
            if node is self.NIL:
                return 1  

            if node.color not in (RED, BLACK):
                raise AssertionError("Propriedade 1 violada: cor de nó inválida.")

            if node.patient.rb_node is not node:
                raise AssertionError(f"Ponteiro rb_node inconsistente no paciente #{node.patient.id}.")

            if min_key is not None and node.key <= min_key:
                raise AssertionError(f"Ordem ABB violada em {node.key} (mínimo {min_key}).")
            if max_key is not None and node.key >= max_key:
                raise AssertionError(f"Ordem ABB violada em {node.key} (máximo {max_key}).")

            if node.left is not self.NIL and node.left.parent is not node:
                raise AssertionError(f"Referência pai incorreta no filho esquerdo de {node.key}.")
            if node.right is not self.NIL and node.right.parent is not node:
                raise AssertionError(f"Referência pai incorreta no filho direito de {node.key}.")

            if node.color == RED and (node.left.color == RED or node.right.color == RED):
                raise AssertionError(f"Propriedade 4 violada: nós rubros consecutivos em {node.key}.")

            visited += 1
            left_bh = _check(node.left, min_key, node.key)
            right_bh = _check(node.right, node.key, max_key)

            if left_bh != right_bh:
                raise AssertionError(f"Propriedade 5 violada: altura-negra divergente em {node.key}.")

            return left_bh + (1 if node.color == BLACK else 0)

        _check(self.root, None, None)

        if visited != self._size:
            raise AssertionError(f"Tamanho inconsistente na Rubro-Negra: {visited} != {self._size}.")

        return True

    def serialize(self) -> dict:
        nodes = []

        def _collect(node: _RBNode) -> None:
            if node is self.NIL:
                return
            _collect(node.left)
            nodes.append(
                {
                    "id": node.patient.id,
                    "name": node.patient.name,
                    "arrival_time": node.patient.arrival_time,
                    "color": "RED" if node.color == RED else "BLACK",
                    "left_id": node.left.patient.id if node.left is not self.NIL else None,
                    "right_id": node.right.patient.id if node.right is not self.NIL else None,
                    "parent_id": node.parent.patient.id if node.parent is not self.NIL else None,
                }
            )
            _collect(node.right)

        _collect(self.root)
        return {
            "size": self._size,
            "height": self.height(),
            "rotations": self.rotations,
            "root_id": self.root.patient.id if self.root is not self.NIL else None,
            "nodes": nodes,
        }