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