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
                locked_and_waiting_files = [f for f in os.listdir(self.lock_dir) if f.endswith('.locked') or f.endswith('.waiting')]
                for file in locked_and_waiting_files:
                    file_path = os.path.join(self.lock_dir, file)
                    if file_path != self.lock_file and file_path != self.wait_file:
                        try:
                            with open(file_path, 'r') as f:
                                timestamp_str = f.read().strip()
                                if timestamp_str:
                                    timestamp = datetime.fromisoformat(timestamp_str)
                                    if datetime.now() - timestamp > self.LOCK_TIMEOUT:
                                        os.remove(file_path)  # Remove expired lock or waiting file
                                        print(f"Expired file {file} removed.")
                        except (ValueError, FileNotFoundError):
                            continue
                if not wait:
                    return False

                # Ensure other applications are not already in "waiting" state
                waiting_files = [f for f in os.listdir(self.lock_dir) if f.endswith('.waiting')]
                if f"{self.app_name}.waiting" not in waiting_files:
                    self.set_status('waiting')
                time.sleep(2)  # Increase delay slightly to prevent busy-looping
                

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
        print("Heartbeat started")

    def _heartbeat(self):
        """
        Heartbeat function to keep the lock file timestamp updated.
        """
        while self.heartbeat_active.is_set() and self.is_locked_by_self():
            with open(self.lock_file, 'w') as f:
                f.write(datetime.now().isoformat())
            time.sleep(self.HEARTBEAT_INTERVAL.total_seconds())
            print("Heartbeat")

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
    lock1 = FileLock("App1", lock_dir='locks')
    if lock1.acquire_lock():
        print("Test 1: App1 acquired lock. SUCCESS!")
        lock1.release_lock()
    else:
        print("Test 1: Basic Lock Acquisition - create a lock for App1")
        print("Expected result: App1 acquires the lock.")
        print("App1 failed to acquire lock. FAIL")
    time.sleep(2)
    print("----------------------------------------------------")
    
    # Test 2: Try to acquire lock for App2 while App1 holds it
    lock1 = FileLock("Test2_App1", lock_dir='locks')
    lock2 = FileLock("Test2_App2", lock_dir='locks')
    lock1.acquire_lock()
    if lock2.acquire_lock():
        print("\nTest 2: Lock Contention - try to acquire lock for App2 while App1 holds it")
        print("Expected result: App2 fails to acquire the lock because App1 is holding it.")
        lock2.release_lock()
        print("App2 acquired lock. FAIL")
    else:
        print("Test 2: App2 failed to acquire lock SUCCESS!")
    lock1.release_lock()
    print("----------------------------------------------------")
    time.sleep(2)

    # Test 3: Releasing and Reacquiring - release lock for App1 and acquire for App2
    
    lock1 = FileLock("Test3_App1")
    lock2 = FileLock("Test3_App2")
    lock1.acquire_lock()
    time.sleep(1)
    lock1.release_lock()
    time.sleep(1)
    if lock2.acquire_lock():
        time.sleep(1)
        lock2.release_lock()
        print("Test 3: App2 acquired lock after App1 released it. SUCCESS")
    else:
        print("\nTest 3: Releasing and Reacquiring - release lock for App1 and acquire for App2")
        print("Expected result: App2 acquires the lock after App1 releases it.")
        print("App2 failed to acquire lock after App1 released it. FAIL")
        
    print("----------------------------------------------------")
    time.sleep(2)

    # Test 4: Waiting Mechanism - simulate App3 waiting and then acquiring lock after App2 releases

    # Define App3's attempt function inline
    def app3_attempt():
        lock3 = FileLock("Test4_App3", lock_dir='locks')
        print("Attempting lock3")
        if lock3.acquire_lock(wait=True):
            print("App3 acquired lock before wait over: FAIL, else: SUCCESSS")
        else:
            print("\nTest 4: Waiting Mechanism with Threads - App3 should wait and acquire lock after App2 releases")
            print("Expected result: App3 waits while App2 holds the lock, then acquires it after App2 releases.")
            print("App3 failed to acquire lock. FAILS")
    # Start App3 in a separate thread
    
    lock2 = FileLock("Test4_App2")
    lock2.acquire_lock()
    app3_thread = threading.Thread(target=app3_attempt)
    app3_thread.start()
    
    time.sleep(2)  # Print(Check waiting lock) - update test code.
    print("Waiting over, release lock. >>")
    lock2.release_lock()
    print("----------------------------------------------------")
    
    # Test 5: Simulate lock timeout
    print("\nTest 5: Simulate lock timeout")
    print("Expected result: App4 acquires the lock initially, the lock times out, and App4 reacquires the lock after timeout.")
    lock4 = FileLock("App4", lock_dir='locks')
    lock4.LOCK_TIMEOUT = timedelta(seconds=5)
    print("lock4.LOCK_TIMEOUT = ", lock4.LOCK_TIMEOUT)
    print ("Locked files =", lock4.is_locked())
    if lock4.acquire_lock(wait=True):
        print("App4 acquired lock before timeout: FAIL, else: SUCCESS!")
    else:
        print("App4 failed to acquire lock. FAIL")
    print("Waiting for lock to timeout...")
    time.sleep(10)
    #if lock4.acquire_lock(wait=True):
    #    print("App4 acquired lock before timeout: FAIL, else: SUCCESSSSUCCESS!")
    #else:
    #    print("App4 failed to reacquire lock after timeout. FAIL")
    lock4.release_lock(force=True)  # Ensure cleanup after test
    
    print("----------------------------------------------------")
