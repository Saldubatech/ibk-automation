import uuid
from typing import Optional, Self

import pandas as pd

from salduba.corvino.persistence.movement_record import MovementRecord, MovementRepo, MovementStatus
from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType
from salduba.util.time import millis_epoch


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
        ibk_type: SecType,
        country: Country,
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
            r.status,
            r.batch,
            r.ticker,
            r.trade,
            r.nombre,
            r.symbol,
            r.raw_type,
            r.ibk_type,
            r.country,
            r.currency,
            r.exchange,
            r.exchange2,
            r.contract_fk,
            r.order_fk
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
            self.ibk_type,
            self.country,
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
            {r.nombre.upper(): Movement.fromRecord(r) for r in movRecords}
        )
