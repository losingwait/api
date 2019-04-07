from threading import Lock

class QueueLocks():
    def __init__(self, **kwargs):
        self.locks = {}
        self.lock = Lock()

    def lockQueue(self, machine_group_id):
        # lock is required to two threads dont try and make the same lock
        self.lock.acquire()
        if machine_group_id not in self.locks:
            self.locks[machine_group_id] = Lock()
        self.lock.release()
        self.locks[machine_group_id].acquire()
        return True

    def unlockQueue(self, machine_group_id):
        # lock is required to check conditional
        self.lock.acquire()
        if machine_group_id not in self.locks:
            self.lock.release()
            return False
        self.lock.release()
        try:
            self.locks[machine_group_id].release()
        except RuntimeError:
            return False
        return True
