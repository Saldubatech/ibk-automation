import datetime
import logging
import os
import tempfile
import unittest
from typing import Any, Tuple

import pandas as pd

from salduba.corvino.parse_input import InputParser
from salduba.corvino.persistence.movement_record import MovementRepo
from salduba.corvino.services.app import CorvinoApp
from salduba.ib_tws_proxy.backing_db.db import DbConfig, TradingDB
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo, DeltaNeutralContractRepo
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRepo, OrderStatusRepo, SoftDollarTierRepo
from salduba.util.files import resolveDir
from salduba.util.logging import init_logging
from salduba.util.tests import testRoot

_maybeTr = testRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(os.path.join(_tr, "resources/logging.yaml"))
_logger = logging.getLogger(__name__)


class TestVerifyContracts(unittest.TestCase):
    @staticmethod
    def repos(db: TradingDB) -> Tuple[ContractRepo, OrderRepo, MovementRepo]:
        dnc_repo = DeltaNeutralContractRepo(db)
        c_repo = ContractRepo(db, dnc_repo)
        orderStRepo = OrderStatusRepo(db)
        sdTRepo = SoftDollarTierRepo(db)
        o_repo = OrderRepo(db, sdTRepo, orderStRepo)
        m_repo = MovementRepo(db, c_repo, o_repo)
        return c_repo, o_repo, m_repo

    def __init__(self, *args: *Any) -> None:
        super().__init__(args[0])
        tmp_file = tempfile.NamedTemporaryFile()
        tmp_file.close()
        tmp_file_path = tmp_file.name
        _logger.info(f"Database File at: {tmp_file_path} for {args[0]}")
        schemata = resolveDir("salduba/ib_tws_proxy/backing_db/schema")
        seed_data = resolveDir("salduba/ib_tws_proxy/backing_db/seed-data")
        if not schemata or not seed_data:
            raise Exception("Schema or Seed Data directories not found")
        self.db_config = DbConfig(
            {
                "path": tmp_file_path,
                "schemas": schemata,
                "seed_data": seed_data,
                "expected_version": "0",
                "target_version": "1",
                "version_date": "2024-02-01 00:00:00.000",
            }
        )
        self.db = TradingDB(self.db_config)
        self.db.configure()
        (
            self.contract_repo,
            self.order_repo,
            self.movement_repo,
        ) = TestVerifyContracts.repos(self.db)
        self.dnc_repo = self.contract_repo._deltaNeutralContractsRepo

    def test_place_orders(self) -> None:
        probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
        probe_all: pd.DataFrame = InputParser.read_csv(probeFile)
        underTest = CorvinoApp(
            self.contract_repo,
            self.dnc_repo,
            self.movement_repo,
            self.order_repo,
            appFamily=1000,
            host="localhost",
            port=7497,
        )

        tmp_file = tempfile.NamedTemporaryFile()
        tmp_file.close()
        output_file_path = tmp_file.name
        _logger.info(f"Output file at: {output_file_path} for {self._testMethodName}")
        probe: pd.DataFrame = probe_all[0:2]

        missing_contracts = underTest.lookup_contracts(inputDF=probe, output_file=output_file_path, ttl=10000)
        if missing_contracts is None:
            result = underTest.placeOrders(
                inputDF=probe,
                batch=f"TestBatch_{datetime.datetime.now().timestamp()}",
                output_file=output_file_path,
            )
            # probeDF = pd.read_csv(probeFile)
            self.assertEqual(f"{len(probe)} Movements Placed", result)
        else:
            self.fail(f"Could not find all contracts, output at: {output_file_path}")
