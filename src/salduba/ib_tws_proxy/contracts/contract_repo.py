import datetime
import logging
from typing import Optional

from ibapi.contract import Contract, DeltaNeutralContract

from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.model import (
    ContractRecord,
    ContractRecordStatus,
    DeltaNeutralContractRecord,
    contractCompanion,
    deltaNeutralCompanion,
)
from salduba.ib_tws_proxy.backing_db.record import RecordMeta
from salduba.ib_tws_proxy.backing_db.repo import Repo
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType

_logger = logging.getLogger(__name__)


class ContractKey:
    @staticmethod
    def resolveContractExchange(exchange: Exchange, exchange2: Exchange) -> Exchange:
        if exchange == Exchange.ISLAND:
            match exchange2:
                case None:
                    return Exchange.NYSE
                case Exchange.UNKNOWN:
                    return Exchange.NYSE
                case Exchange.NONE:
                    return Exchange.NYSE
                case _:
                    return exchange2
        else:
            return exchange

    def __init__(
        self,
        symbol: str,
        secType: SecType,
        exchange: Exchange,
        exchange2: Exchange,
        currency: Currency,
    ):
        self.symbol = symbol
        self.secType = secType
        self.exchange = ContractKey.resolveContractExchange(exchange, exchange2)
        self.currency = currency

    def contractPattern(self) -> Contract:
        contract = Contract()
        contract.symbol = self.symbol
        contract.secType = self.secType
        contract.exchange = self.exchange
        contract.currency = self.currency
        return contract


class DeltaNeutralContractRepo(Repo[RecordMeta, DeltaNeutralContractRecord]):
    def __init__(self, db: TradingDB):
        super().__init__(db, deltaNeutralCompanion, DeltaNeutralContractRecord.hydrate)


def contractFromRecord(record: ContractRecord, dnc: Optional[DeltaNeutralContract] = None) -> Contract:
    contract: Contract = Contract()
    contract.expires_on = record.expires_on  # type: ignore
    contract.status = record.status  # type: ignore
    contract.conId = record.conid  # type: ignore
    contract.symbol = record.symbol  # type: ignore
    contract.secType = record.sec_type  # type: ignore
    contract.lastTradeDateOrContractMonth = record.last_trade_date_or_contract_month  # type: ignore
    contract.strike = record.strike  # type: ignore
    contract.right = record.right  # type: ignore
    contract.multiplier = record.multiplier  # type: ignore
    contract.exchange = record.exchange  # type: ignore
    contract.currency = record.currency  # type: ignore
    contract.localSymbol = record.local_symbol  # type: ignore
    contract.primaryExchange = record.primary_exchange  # type: ignore
    contract.tradingClass = record.trading_class  # type: ignore
    contract.includeExpired = record.include_expired  # type: ignore
    contract.secIdType = record.sec_id_type  # type: ignore
    contract.secId = record.sec_id  # type: ignore
    contract.description = record.description  # type: ignore
    contract.issuerId = record.issuer_id  # type: ignore
    contract.comboLegsDescrip = record.combo_legs_description  # type: ignore
    contract.deltaNeutralContract = dnc
    return contract


class ContractRepo(Repo[RecordMeta, ContractRecord]):
    contract_shelf_life = 3 * 30 * 24 * 3600 * 1000

    def __init__(self, db: TradingDB, deltaNeutralContractRepo: DeltaNeutralContractRepo) -> None:
        #  error: Argument 3 to "__init__" of "Repo" has incompatible type "Callable[[VarArg(list[str])], ContractRecord]";
        #  expected "Callable[[Iterable[Any]], ContractRecord]"
        super().__init__(db, contractCompanion, ContractRecord.hydrate)  # type: ignore
        self._deltaNeutralContractsRepo = deltaNeutralContractRepo

    def findNominalContract(
        self,
        symbol: str,
        ibk_type: str,
        exchange: str,
        exchange2: str,
        currency: str,
        atTime: int,
    ) -> Optional[ContractRecord]:
        conditions = [
            ContractRecord.expiresAfterClause,
            ContractRecord.symbolClause,
            ContractRecord.secTypeClause,
            f"({ContractRecord.exchangeClause} or {ContractRecord.exchangeClause})",
            ContractRecord.currencyClause,
            ContractRecord.statusClause,
        ]
        parameters = [
            atTime,
            symbol,
            ibk_type,
            exchange,
            exchange2,
            currency,
            ContractRecordStatus.NOMINAL,
        ]
        _logger.debug(f"Lookup Symbol {symbol} with condition {conditions} and parameters {parameters}")
        found: list[ContractRecord] = self.select(parameters, conditions)
        _logger.debug(f"\t With Result: {found}")
        if found and len(found) > 1:
            _logger.error(f"\tMore than one ContractRecord found for {symbol} at {exchange}:\n\t{found}")
            raise Exception(f"Found more than one NOMINAL contract record for {symbol} with expiration later than {atTime}")
        return found[0] if found else None

    def registerUpdate(self, updated: ContractRecord) -> ContractRecord:
        at: int = int(datetime.datetime.now().timestamp() * 1000)
        preExisting = self.findNominalContract(
            updated.symbol, updated.ibk_type, updated.exchange, updated.exchange2, updated.currency, at  # type: ignore
        )
        if preExisting:
            preExisting.status = ContractRecordStatus.RETIRED  # type: ignore
            preExisting.at = at
            with self.db as db:
                with db.cursor():
                    self.update(preExisting)
                    updated.expires_on = at + ContractRepo.contract_shelf_life  # type: ignore
                    updated.at = at
                    self.insert([updated])
        return updated
