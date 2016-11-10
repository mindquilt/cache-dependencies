import threading
from cache_tagging import interfaces


class DependencyLock(interfaces.IDependencyLock):

    def __init__(self, thread_safe_cache_accessor, delay=0):
        self._cache = thread_safe_cache_accessor
        self._delay = delay  # For master/slave

    def evaluate(self, dependency, transaction_start_time, version):
        dependency.evaluate(self._cache(), transaction_start_time, version)

    @staticmethod
    def make(isolation_level, thread_safe_cache_accessor, delay):
        if isolation_level == 'READ UNCOMMITTED':
            return ReadUncommittedDependencyLock(thread_safe_cache_accessor, delay)
        elif isolation_level == 'READ COMMITTED':
            return ReadCommittedDependencyLock(thread_safe_cache_accessor, delay)
        elif isolation_level == 'REPEATABLE READ':
            return RepeatableReadDependencyLock(thread_safe_cache_accessor, delay)
        elif isolation_level == 'SERIALIZABLE':
            return SerializableDependencyLock(thread_safe_cache_accessor, delay)
        else:
            raise ValueError(isolation_level)


class ReadUncommittedDependencyLock(DependencyLock):
    """Tag Lock for Read Uncommitted transaction isolation level."""
    def acquire(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """

    def release(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        if self._delay:
            return self._release_dependency_delayed(dependency, version)

    def _release_dependency_delayed(self, dependency, version):
        return threading.Timer(self._delay, self._release_dependency_target, [dependency, version]).start()

    def _release_dependency_target(self, dependency, version):
        dependency.invalidate(self._cache(), version)


class ReadCommittedDependencyLock(ReadUncommittedDependencyLock):
    """Tag Lock for Read Committed transaction isolation level."""
    def release(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        self._release_dependency_target(dependency, version)
        super(ReadCommittedDependencyLock, self).release(dependency, version)


class RepeatableReadDependencyLock(DependencyLock):
    """Tag Lock for Repeatable Reads transaction isolation level."""
    def acquire(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        dependency.acquire(self._cache(), self._delay, version)

    def release(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        dependency.release(self._cache(), self._delay, version)


class SerializableDependencyLock(RepeatableReadDependencyLock):
    """Tag Lock for Serializable transaction isolation level."""
