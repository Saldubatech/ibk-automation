import logging
import os
import time

log_dir: str = "log"
prefix: str = "ib_tws_proxy"


class LocalLogger:
    def __init__(
        self,
        path: str = "log",
        recordFormat: str = "(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s",
        timeFormat: str = "%y%m%d_%H:%M:%S",
        level: int = logging.INFO,
    ) -> None:
        if not os.path.exists(path):
            os.makedirs(path)

        time.strftime(f"{prefix}.%Y%m%d_%H%M%S.log")

        # logging.basicConfig( level=logging.DEBUG,
        #                    format=recordFormat, datefmt=timeFormat)
        logging.basicConfig(
            filename=time.strftime(f"{log_dir}/{prefix}.{timeFormat}.log"),
            filemode="w",
            level=logging.INFO,
            format=recordFormat,
            datefmt=timeFormat,
        )
        logger = logging.getLogger()
        self.console = logging.StreamHandler()
        self.console.setLevel(level)
        logger.addHandler(self.console)

    def setLevel(self, level: int) -> None:
        self.console.setLevel(level)
