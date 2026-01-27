import ssl
import time
import asyncio
import aiohttp

from typing import Final
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass(slots=True)
class CheckResult:
    url: str
    is_up: bool = False
    status_code: int | None = None
    response_time_ms: int = 0
    error: str | None = None
    ssl_expires_at: datetime | None = None
    ssl_days_left: int | None = None


class NetworkClient:
    """
    Клиент для асинхронной проверки доступности веб-ресурсов
    и получения информации об SSL сертификатах.
    """

    _CERT_TIME_FMT: Final[str] = "%b %d %H:%M:%S %Y %Z"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self._connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(
            timeout=self._timeout, connector=self._connector
        )

    async def close(self) -> None:
        await self._session.close()
        await self._connector.close()

    async def check_url(self, url: str) -> CheckResult:
        result = CheckResult(url=url)
        start_time = time.perf_counter()

        try:
            # Используем GET, чтобы получить и заголовки, и тело
            async with self._session.get(url) as response:
                result.status_code = response.status
                # Считаем сайт живым, если код < 500
                result.is_up = 200 <= response.status < 500

                # Извлечение SSL сертификата
                if (
                    url.startswith("https://")
                    and response.connection
                    and response.connection.transport
                ):
                    ssl_object = response.connection.transport.get_extra_info(
                        "ssl_object"
                    )
                    if ssl_object:
                        cert = ssl_object.getpeercert(binary_form=False)
                        not_after = cert.get("notAfter") if cert else None
                        if not_after:
                            expires_at = datetime.strptime(
                                not_after, self._CERT_TIME_FMT
                            ).replace(tzinfo=timezone.utc)
                            result.ssl_expires_at = expires_at
                            result.ssl_days_left = (
                                expires_at - datetime.now(timezone.utc)
                            ).days

        except asyncio.TimeoutError:
            result.error = "Connection timed out"
        except aiohttp.ClientError as e:
            result.error = str(e)
        except Exception as e:
            result.error = str(e)
        finally:
            result.response_time_ms = int((time.perf_counter() - start_time) * 1000)

        return result
