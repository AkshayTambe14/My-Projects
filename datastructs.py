class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0 

    def __iter__(self):
            current = self.head
            while current:
                yield current.data
                current = current.next
    
    def __len__(self):
        return self._size
                
    def append(self, data):
        node = Node(data)
        if not self.head:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1


class Queue(LinkedList):
    def enqueue(self, data):
        self.append(data)

    def dequeue(self):
        if not self.head:
            return None

        node = self.head
        self.head = self.head.next

        if not self.head:
            self.tail = None

        self._size = max(0, self._size - 1)
        return node.data

    def is_empty(self):
        return self.head is None
    
    