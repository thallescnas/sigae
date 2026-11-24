class MinHeap:
    def __init__(self, key_fn):
        self._items: list = []
        self._key_fn = key_fn

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def _swap(self, i: int, j: int) -> None:
        self._items[i], self._items[j] = self._items[j], self._items[i]
        self._items[i].heap_index = i
        self._items[j].heap_index = j

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self._key_fn(self._items[index]) < self._key_fn(self._items[parent]):
                self._swap(index, parent)
                index = parent
            else:
                break

    def _sift_down(self, index: int) -> None:
        n = len(self._items)
        while True:
            left = 2 * index + 1
            right = left + 1
            smallest = index

            if left < n and self._key_fn(self._items[left]) < self._key_fn(self._items[smallest]):
                smallest = left
            if right < n and self._key_fn(self._items[right]) < self._key_fn(self._items[smallest]):
                smallest = right

            if smallest == index:
                break

            self._swap(index, smallest)
            index = smallest

    def insert(self, item) -> None:
        if item.heap_index != -1:
            raise ValueError(f"Item já está no Heap (índice {item.heap_index}).")
        index = len(self._items)
        self._items.append(item)
        item.heap_index = index
        self._sift_up(index)

    def peek(self):
        return self._items[0] if self._items else None

    def extract_min(self):
        if not self._items:
            return None
        root = self._items[0]
        self.remove(root)
        return root

    def remove(self, item) -> bool:
        index = item.heap_index
        if index < 0 or index >= len(self._items) or self._items[index] is not item:
            return False

        last_index = len(self._items) - 1
        if index != last_index:
            self._swap(index, last_index)

        removed = self._items.pop()
        removed.heap_index = -1

        if index < len(self._items):
            self._sift_up(index)
            self._sift_down(self._items[index].heap_index)

        return True

    def update_item(self, item) -> None:
        index = item.heap_index
        if index < 0 or index >= len(self._items) or self._items[index] is not item:
            raise ValueError("Item não encontrado no Heap para atualização.")
        self._sift_up(index)
        self._sift_down(item.heap_index)

    def all_items(self) -> list:
        return list(self._items)

    def clear(self) -> None:
        for item in self._items:
            item.heap_index = -1
        self._items.clear()

    def validate(self) -> bool:
        for i, item in enumerate(self._items):
            if item.heap_index != i:
                raise AssertionError(f"heap_index inconsistente: esperado {i}, obtido {item.heap_index}")
            if i > 0:
                parent = (i - 1) // 2
                if self._key_fn(self._items[parent]) > self._key_fn(item):
                    raise AssertionError(f"Propriedade de Min-Heap violada entre índices {parent} e {i}")
        return True

    def serialize(self) -> list[dict]:
        return [
            item.to_dict() if hasattr(item, "to_dict") else {"value": item}
            for item in self._items
        ]