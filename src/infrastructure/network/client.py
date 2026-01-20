import ssl
import time
import asyncio
import aiohttp

from datetime import datetime
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

    def __init__(self, timeout: int = 10):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def check_url(self, url: str) -> CheckResult:
        result = CheckResult(url=url)
        start_time = time.perf_counter()

        try:
            # Создаем SSL контекст, который не проверяет валидность цепочки (check_hostname=False),
            # чтобы мы могли получить данные сертификата даже если он просрочен или самоподписан.
            # Но для продакшена лучше использовать verify_mode=ssl.CERT_REQUIRED если нужна строгость.
            # Здесь цель - мониторинг, так что нам важнее получить данные, чем упасть с ошибкой.
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)

            async with aiohttp.ClientSession(
                timeout=self.timeout, connector=connector
            ) as session:
                # Используем GET, чтобы получить и заголовки, и тело
                async with session.get(url) as response:
                    result.status_code = response.status
                    # Считаем сайт живым, если код < 500 (даже 404 означает, что сервер отвечает)
                    result.is_up = 200 <= response.status < 400

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
                            if cert and "notAfter" in cert:
                                # Формат даты: 'May 25 12:00:00 2024 GMT'
                                date_str = cert["notAfter"]
                                expires_at = datetime.strptime(
                                    date_str, "%b %d %H:%M:%S %Y %Z"
                                )
                                result.ssl_expires_at = expires_at
                                result.ssl_days_left = (
                                    expires_at - datetime.utcnow()
                                ).days

            # Расчет времени отклика
            end_time = time.perf_counter()
            result.response_time_ms = int((end_time - start_time) * 1000)

        except asyncio.TimeoutError:
            result.is_up = False
            result.error = "Connection timed out"

        except Exception as e:
            result.is_up = False
            result.error = str(e)

        return result
