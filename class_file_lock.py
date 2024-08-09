import os
import time
from datetime import datetime, timedelta
import threading

class FileLock:
    LOCK_TIMEOUT = timedelta(minutes=5)
    HEARTBEAT_INTERVAL = timedelta(seconds=10)

    def __init__(self, app_name, lock_dir='.'):
        """
        Initializes the FileLock instance.
        :param app_name: Name of the application using the lock.
        :param lock_dir: Directory where lock files will be stored.
        """
        self.app_name = app_name
        self.lock_file = os.path.join(lock_dir, f"{app_name}.locked")
        self.wait_file = os.path.join(lock_dir, f"{app_name}.waiting")
        self.lock_dir = lock_dir
        self.heartbeat_thread = None
        self.heartbeat_active = threading.Event()
        if not os.path.exists(lock_dir):
            os.makedirs(lock_dir)

    def is_locked(self):
        """
        Checks if the lock is held by any application other than the current one.
        :return: True if any lock file exists other than the current application's lock file, False otherwise.
        """
        locked_files = [f for f in os.listdir(self.lock_dir) if f.endswith('.locked')]
        return any(f != os.path.basename(self.lock_file) for f in locked_files)

    def is_waiting(self, waiting_file):
        """
        Checks if waiting is held by the named application.
        :return: True if waiting file held by named application, False otherwise.
        """
        print(f"Check waiting file name = {os.path.basename(waiting_file)}")
        waiting_files = [f for f in os.listdir(self.lock_dir) if f.endswith('.waiting')]
        print("waiting files found = ", waiting_files)
        return any(f == os.path.basename(waiting_file) for f in waiting_files)

    def get_lock_status(self):
        """
        Checks if the lock is held by any application other than the current one.
        :return: True if any lock or wait file exists other than the current application's lock file, False otherwise.
        """
        locked_files = [f for f in os.listdir(self.lock_dir)]
        return any(f != os.path.basename(self.lock_file) for f in locked_files)

    def get_lock_files(self):
        """
        Checks if the lock is held by any application other than the current one.
        :return: Files if any lock or wait file exists other than the current application's lock file, False otherwise.
        """
        locked_files = [f for f in os.listdir(self.lock_dir)]
        return locked_files

    def set_status(self, status):
        """
        Sets the status of the application (locked or waiting) by creating a respective file.
        :param status: Status of the application ('locked' or 'waiting').
        """
        is_waiting=self.is_waiting(self.wait_file)
        file_path = self.lock_file if status == 'locked' else os.path.join(self.lock_dir, f"{self.app_name}.waiting")
        print ("'is_waiting' = ", is_waiting)
        if is_waiting:
            try:
                print ("Replace old wait file")
                os.replace(self.wait_file, file_path)
            except FileNotFoundError:
                pass
        with open(file_path, 'w') as f:
            f.write(datetime.now().isoformat())
        print(datetime.now().isoformat(),":",file_path, "New lock applied")

    def acquire_lock(self, wait=False):
        """
        Attempts to acquire the lock for the current application.
        :wait: Accepts True or False. True indicates wait for lock and ask for other application to free up (via the "waiting" file).
        :return: True if the lock was successfully acquired, False otherwise.
        """
        while True:
            if not self.is_locked():
                self.set_status('locked')
                self._start_heartbeat()
                return True
            else:
                # Check for lock timeout
                locked_files = [f for f in os.listdir(self.lock_dir) if f.endswith('.locked')]
                for locked_file in locked_files:
                    if locked_file != os.path.basename(self.lock_file):
                        try:
                            with open(os.path.join(self.lock_dir, locked_file), 'r') as f:
                                lock_time_str = f.read().strip()
                                if lock_time_str:
                                    lock_time = datetime.fromisoformat(lock_time_str)
                                    if datetime.now() - lock_time > self.LOCK_TIMEOUT:
                                        self.release_lock(force=True)
                        except (ValueError, FileNotFoundError):
                            continue
                if not wait:
                    return False
                self.set_status('waiting')
                time.sleep(1)
                

    def release_lock(self, force=False):
        """
        Releases the lock held by the current application.
        :param force: If True, forces the release even if the lock file is not found.
        """
        try:
            os.remove(self.wait_file)
        except FileNotFoundError:
            pass
        try:
            os.remove(self.lock_file)
        except FileNotFoundError:
            if not force:
                raise

        print(datetime.now().isoformat(),":",self.lock_file, "Released")
        # Promote the next waiting application to locked status
        #waiting_apps = sorted(f for f in os.listdir(self.lock_dir) if f.endswith('.waiting'))
        #if waiting_apps:
        #    next_app = waiting_apps[0].split('.')[0]
        #    next_lock_file = os.path.join(self.lock_dir, f"{next_app}.locked")
        #    os.rename(os.path.join(self.lock_dir, f"{next_app}.waiting"), next_lock_file)
        #    with open(next_lock_file, 'w') as f:
        #        f.write(datetime.now().isoformat())

        # Stop the heartbeat thread
        self.heartbeat_active.clear()
        if self.heartbeat_thread:
            self.heartbeat_thread.join()

    def _start_heartbeat(self):
        """
        Starts the heartbeat thread to periodically update the lock file timestamp.
        """
        self.heartbeat_active.set()
        self.heartbeat_thread = threading.Thread(target=self._heartbeat)
        self.heartbeat_thread.start()

    def _heartbeat(self):
        """
        Heartbeat function to keep the lock file timestamp updated.
        """
        while self.heartbeat_active.is_set() and self.is_locked_by_self():
            with open(self.lock_file, 'w') as f:
                f.write(datetime.now().isoformat())
            time.sleep(self.HEARTBEAT_INTERVAL.total_seconds())

    def is_locked_by_self(self):
        """
        Checks if the current application holds the lock.
        :return: True if the current application holds the lock, False otherwise.
        """
        try:
            with open(self.lock_file, 'r') as f:
                lock_time_str = f.read().strip()
                if lock_time_str:
                    lock_time = datetime.fromisoformat(lock_time_str)
                    return datetime.now() - lock_time < self.HEARTBEAT_INTERVAL * 2
        except (ValueError, FileNotFoundError):
            pass
        return False

if __name__ == "__main__":
    # Test Plan

    # Test 1: Create a lock for App1
    print("Test 1: Create a lock for App1")
    print("Expected result: App1 acquires the lock.")
    lock1 = FileLock("App1", lock_dir='locks')
    if lock1.acquire_lock():
        print("App1 acquired lock.")
    else:
        print("App1 failed to acquire lock.")
    time.sleep(2)

    # Test 2: Try to acquire lock for App2 while App1 holds it
    print("\nTest 2: Try to acquire lock for App2 while App1 holds it")
    print("Expected result: App2 fails to acquire the lock because App1 is holding it.")
    lock2 = FileLock("App2", lock_dir='locks')
    if lock2.acquire_lock():
        print("App2 acquired lock.")
    else:
        print("App2 failed to acquire lock.")
    time.sleep(2)

    # Test 3: Release lock for App1 and acquire for App2
    print("\nTest 3: Release lock for App1 and acquire for App2")
    print("Expected result: App2 acquires the lock after App1 releases it.")
    lock1.release_lock()
    if lock2.acquire_lock():
        print("App2 acquired lock after App1 released it.")
    else:
        print("App2 failed to acquire lock after App1 released it.")
    time.sleep(2)

    # Test 4: Simulate App3 waiting and then acquiring lock after App2 releases
    print("\nTest 4: Simulate App3 waiting and then acquiring lock after App2 releases")
    print("Expected result: App3 fails to acquire the lock initially, but succeeds after App2 releases it.")
    lock3 = FileLock("App3", lock_dir='locks')
    if lock3.acquire_lock():
        print("App3 acquired lock.")
    else:
        print("App3 failed to acquire lock.")
    lock2.release_lock()
    time.sleep(2)
    if lock3.acquire_lock():
        print("App3 acquired lock after App2 released it.")
    else:
        print("App3 failed to acquire lock after App2 released it.")

    # Test 5: Simulate lock timeout
    print("\nTest 5: Simulate lock timeout")
    print("Expected result: App4 acquires the lock initially, the lock times out, and App4 reacquires the lock after timeout.")
    lock4 = FileLock("App4", lock_dir='locks')
    lock4.LOCK_TIMEOUT = timedelta(seconds=5)
    if lock4.acquire_lock():
        print("App4 acquired lock.")
    else:
        print("App4 failed to acquire lock.")
    print("Waiting for lock to timeout...")
    time.sleep(10)
    if lock4.acquire_lock():
        print("App4 reacquired lock after timeout.")
    else:
        print("App4 failed to reacquire lock after timeout.")
    lock4.release_lock(force=True)  # Ensure cleanup after test
