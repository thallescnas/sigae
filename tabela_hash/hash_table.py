class _HashNode:
    __slots__ = ("key", "value", "next")

    def __init__(self, key: int, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node
def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True
def _next_prime(n: int) -> int:
    candidate = n if n % 2 != 0 else n + 1
    while not _is_prime(candidate):
        candidate += 2
    return candidate

class HashTable:
    def __init__(self, initial_capacity: int = 11, max_load_factor: float = 0.75):
        self._initial_capacity = initial_capacity
        self._capacity = initial_capacity
        self._max_load_factor = max_load_factor
        self._buckets: list[_HashNode | None] = [None] * self._capacity
        self._size = 0
        self.collisions = 0
        self.rehash_count = 0

    def _hash(self, key: int) -> int:
        return key % self._capacity

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity if self._capacity else 0.0
    
    def __len__(self) -> int:
        return self._size

    def get(self, key: int):
        idx = self._hash(key)
        node = self._buckets[idx]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        return None

    def contains(self, key: int) -> bool:
        return self.get(key) is not None
    
    def put(self, key: int, value) -> None:
        if self.contains(key):
            raise ValueError(f"Chave duplicada na Tabela Hash: {key}")

        if (self._size + 1) / self._capacity > self._max_load_factor:
            self._rehash()

        idx = self._hash(key)
        if self._buckets[idx] is not None:
            self.collisions += 1

        new_node = _HashNode(key, value, self._buckets[idx])
        self._buckets[idx] = new_node
        self._size += 1

    def remove(self, key: int):
        idx = self._hash(key)
        prev = None
        curr = self._buckets[idx]

        while curr is not None:
            if curr.key == key:
                if prev is None:
                    self._buckets[idx] = curr.next
                else:
                    prev.next = curr.next
                self._size -= 1
                return curr.value
            prev = curr
            curr = curr.next

        return None

    def _rehash(self) -> None:
        old_buckets = self._buckets
        self._capacity = _next_prime(self._capacity * 2 + 1)
        self._buckets = [None] * self._capacity
        self._size = 0
        self.rehash_count += 1

        for head in old_buckets:
            curr = head
            while curr is not None:
                next_node = curr.next
                idx = self._hash(curr.key)
                if self._buckets[idx] is not None:
                    self.collisions += 1
                curr.next = self._buckets[idx]
                self._buckets[idx] = curr
                self._size += 1
                curr = next_node

    def values(self) -> list:
        result = []
        for head in self._buckets:
            curr = head
            while curr is not None:
                result.append(curr.value)
                curr = curr.next
        return result

    def clear(self) -> None:
        self._capacity = self._initial_capacity
        self._buckets = [None] * self._capacity
        self._size = 0
        self.collisions = 0
        self.rehash_count = 0
    def validate(self) -> bool:
        count = 0
        seen_keys = []
        for idx, head in enumerate(self._buckets):
            curr = head
            while curr is not None:
                if self._hash(curr.key) != idx:
                    raise AssertionError(f"Chave {curr.key} no bucket incorreto {idx}")
                if curr.key in seen_keys:
                    raise AssertionError(f"Chave duplicada encontrada na Hash: {curr.key}")
                seen_keys.append(curr.key)
                count += 1
                curr = curr.next
        if count != self._size:
            raise AssertionError(f"Tamanho inconsistente na Hash: {count} != {self._size}")
        return True

    def serialize(self) -> dict:
        buckets_data = []
        for idx, head in enumerate(self._buckets):
            items = []
            curr = head
            while curr is not None:
                items.append(curr.value.to_dict() if hasattr(curr.value, "to_dict") else curr.key)
                curr = curr.next
            buckets_data.append({"index": idx, "items": items})

        return {
            "capacity": self._capacity,
            "size": self._size,
            "load_factor": round(self.load_factor, 3),
            "collisions": self.collisions,
            "rehash_count": self.rehash_count,
            "buckets": buckets_data,
        }