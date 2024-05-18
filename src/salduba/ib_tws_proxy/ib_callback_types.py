from typing import Callable

from ibapi.contract import ContractDescription

SymbolSamples = Callable[[int, list[ContractDescription]], None]

FundamentalData = Callable[[int, str], None]
