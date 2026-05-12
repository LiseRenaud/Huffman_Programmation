import heapq

# classe de la file de priorité utilisée pour construire l'arbre de Huffman,
class PriorityQueue:

    # la file de priorité est implémentée à l'aide d'une liste et de la bibliothèque heapq pour maintenir l'ordre des éléments en fonction de leur priorité ici leur fréquence.
    def __init__(self):
        self._queue = []
        self._index = 0

    # la méthode push ajoute un élément à la file de priorité avec une priorité donnée, en utilisant heapq.heappush pour maintenir l'ordre des éléments.
    def push(self, item, priority):
        heapq.heappush(self._queue, (priority, self._index, item))
        self._index += 1

    # la méthode pop extrait l'élément de plus haute priorité cad celui avec la plus petite fréquence.
    def pop(self):
        if not self._queue:
            raise IndexError("pop from an empty priority queue")
        priority, index, item = heapq.heappop(self._queue)
        return item

    def is_empty(self):
        return len(self._queue) == 0