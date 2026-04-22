import datetime
import functools
import json
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, message: str, func_name: str, block_time: datetime.datetime):
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time


def validate_args(critical_count: int = 5, time_to_recover: int = 30) -> None:
    errors: list[Exception] = []
    if critical_count < 1 or not isinstance(critical_count, int):
        errors.append(ValueError(INVALID_CRITICAL_COUNT))
    if time_to_recover < 1 or not isinstance(time_to_recover, int):
        errors.append(ValueError(INVALID_RECOVERY_TIME))
    if len(errors) != 0:
        raise ExceptionGroup(VALIDATIONS_FAILED, errors)


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        validate_args(critical_count, time_to_recover)
        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self.__error_count = 0

        self.__unblock_time: datetime.datetime | None = None
        self.__block_time: datetime.datetime

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            full_func_name = f"{func.__module__}.{func.__name__}"

            self.check_state(full_func_name)

            try:
                res = func(*args, **kwargs)
            except self.triggers_on as error:
                self.handle_failure(full_func_name, error)

            self.handle_success()
            return res

        return wrapper

    def check_state(self, full_func_name: str) -> None:
        if self.__error_count < self.critical_count or not self.__unblock_time:
            return

        now = datetime.datetime.now(datetime.UTC)
        if now < self.__unblock_time:
            raise BreakerError(TOO_MUCH, full_func_name, self.__block_time)

        self.__error_count = 0

    def handle_success(self) -> None:
        self.__error_count = 0
        self.__unblock_time = None

    def handle_failure(self, full_func_name: str, original_error: Exception) -> None:
        self.__error_count += 1

        if self.__error_count >= self.critical_count:
            now = datetime.datetime.now(datetime.UTC)
            self.__block_time = now
            self.__unblock_time = now + datetime.timedelta(seconds=self.time_to_recover)

            raise BreakerError(TOO_MUCH, full_func_name, self.__block_time) from original_error
        raise original_error


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
