from threading import Lock

class QueueLocks():
    def __init__(self, **kwargs):
        self.locks = {}
        self.lock = Lock()

    def lockQueue(self, machine_group_id):
        self.lock.acquire()
        if machine_group_id not in self.locks:
            self.locks[machine_group_id] = Lock()
        self.locks[machine_group_id].acquire()
        self.lock.release()
        return True

    def unlockQueue(self, machine_group_id):
        self.lock.acquire()
        if machine_group_id not in self.locks:
            self.lock.release()
            return False
        self.locks[machine_group_id].release()
        self.lock.release()
        return True
