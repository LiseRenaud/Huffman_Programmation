import heapq

class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0  # To maintain order for same-priority items

    def push(self, item, priority):
        # Lower priority value means higher priority
        heapq.heappush(self._queue, (priority, self._index, item))
        self._index += 1

    def pop(self):
        if not self._queue:
            raise IndexError("pop from an empty priority queue")
        priority, index, item = heapq.heappop(self._queue)
        return item

    def is_empty(self):
        return len(self._queue) == 0