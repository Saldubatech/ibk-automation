import uuid
from enum import StrEnum
from typing import Optional, Self

import pandas as pd

from salduba.corvino.persistence.movement_record import MovementRecord, MovementRepo
from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType
from salduba.util.time import millis_epoch


class MovementStatus(StrEnum):
    NEW = "New"
    SUBMITTED = "Submitted"
    CONFIRMED = "Confirmed"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    API_ERROR = "Error"

    @classmethod
    def fromIbk(cls, ibk_order_status: str) -> "MovementStatus":
        # https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#a27ec36f07dff982f50968c8a8887d676
        match ibk_order_status:
            case "PendingSubmit":
                return MovementStatus.SUBMITTED
            case "PendingCancel":
                return MovementStatus.CONFIRMED
            case "PreSubmitted":
                return MovementStatus.CONFIRMED
            case "Submitted":
                return MovementStatus.CONFIRMED
            case "Cancelled":
                return MovementStatus.CANCELLED
            case "Filled":
                return MovementStatus.COMPLETED
            case "Inactive":
                return MovementStatus.CANCELLED
            case _:
                return MovementStatus.API_ERROR


class Movement:
    def __repr__(self) -> str:
        return repr(self.__dict__)

    # error: Missing type parameters for generic type "Series"
    @classmethod
    def fromDFRow(cls, batch: str, r: pd.Series, contractRid: str) -> Self:  # type: ignore
        return cls(
            MovementStatus.NEW,
            batch,
            r["Ticker"],
            r["Trade"],
            r["Nombre"],
            r["Symbol"],
            r["RawType"],
            r["Country"],
            r["IbkType"],
            r["Currency"],
            r["Exchange"],
            r["Exchange2"],
            contractRid,
            None,
        )

    def __init__(
        self,
        status: MovementStatus,
        batch: str,
        ticker: str,
        trade: int,
        name: str,
        symbol: str,
        raw_type: str,
        country: Country,
        ibk_type: SecType,
        currency: Currency,
        exchange: Exchange,
        exchange2: Optional[Exchange],
        contract_key: str,
        order_key: Optional[str],
    ) -> None:
        self.status = status
        self.batch = batch
        self.ticker = ticker
        self.trade = trade
        self.name = name
        self.symbol = symbol
        self.raw_type = raw_type
        self.country = country
        self.ibk_type = ibk_type
        self.currency = currency
        self.exchange = exchange
        self.exchange2 = exchange2
        self.contract_key = contract_key
        self.order_key = order_key

    @classmethod
    def fromRecord(cls, r: MovementRecord) -> Self:
        rs = cls(
            r.status,  # type: ignore
            r.batch,  # type: ignore
            r.ticker,  # type: ignore
            r.trade,  # type: ignore
            r.nombre,  # type: ignore
            r.symbol,  # type: ignore
            r.raw_type,  # type: ignore
            r.country,  # type: ignore
            r.ibk_type,  # type: ignore
            r.currency,  # type: ignore
            r.exchange,  # type: ignore
            r.exchange2,  # type: ignore
            r.contract_fk,  # type: ignore
            r.order_fk,  # type: ignore
        )
        return rs

    def resolveContractExchange(self) -> Exchange:
        if self.exchange == Exchange.ISLAND:
            match self.exchange2:
                case None:
                    return Exchange.NYSE
                case Exchange.UNKNOWN:
                    return Exchange.NYSE
                case Exchange.NONE:
                    return Exchange.NYSE
                case _:
                    return self.exchange2
        else:
            return self.exchange

    def newRecord(self) -> MovementRecord:
        # Create a MovementRecord from this object with a fresh `Id`.
        return MovementRecord(
            str(uuid.uuid4()),
            millis_epoch(),
            self.status,
            self.batch,
            self.ticker,
            self.trade,
            self.name,
            self.symbol,
            self.raw_type,
            self.country,
            self.ibk_type,
            self.currency,
            self.exchange,
            self.exchange2,
            self.contract_key,
            self.order_key,
        )


class MovementBatch:
    movements_excel_sheet: str = "Movements"

    def __init__(self, batch: str, movements: dict[str, Movement]):
        self.batch = batch
        self.movements: dict[str, Movement] = movements

    def persist(self, repo: MovementRepo) -> None:
        if self.movements:
            with repo.db as db:
                with db.cursor():
                    if not repo.doesBatchExist(self.batch):
                        repo.insert([m.newRecord() for m in self.movements.values()])

    @classmethod
    def fromRepo(cls, repo: MovementRepo, batch: str) -> Self:
        movRecords = repo.forBatch(batch)
        return cls(
            batch,
            {r.nombre.upper(): Movement.fromRecord(r) for r in movRecords},  # type: ignore
        )
