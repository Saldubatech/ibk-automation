# -*- coding: utf-8 -*-
import datetime
import tempfile
import unittest
from uuid import uuid4

from salduba.ib_tws_proxy.backing_db.db import DbConfig, TradingDB
from salduba.ib_tws_proxy.backing_db.model import ContractRecord, ContractRecordStatus, contractCompanion

expected_db_version = 1
expected_tables = {
    "DB_INFO",
    "DELTA_NEUTRAL_CONTRACT",
    "CONTRACT",
    "COMBO_LEG",
    "CONTRACT_DETAIL_TAG",
    "CONTRACT_DETAILS",
    "MOVEMENT",
}


class TestModel(unittest.TestCase):
    "Test the Model Records"

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)
        self.config = DbConfig(
            {
                "path": "tests/resources/test_db.db",
                "schemas": "salduba/ib_tws_proxy/backing_db/schema",
                "seed_data": "salduba/ib_tws_proxy/backing_db/seed-data",
                "expected_version": "0",
                "target_version": "1",
                "version_date": "2024-02-01 00:00:00.000",
            }
        )
        self.db = TradingDB(self.config)

    def __local_db__(self) -> TradingDB:
        temp = tempfile.NamedTemporaryFile()
        temp.close()
        local_config = DbConfig(
            {
                "path": temp.name,
                "schemas": "salduba/ib_tws_proxy/backing_db/schema",
                "seed_data": "salduba/ib_tws_proxy/backing_db/seed-data",
                "expected_version": "0",
                "target_version": "1",
                "version_date": "2024-02-01 00:00:00.000",
            }
        )
        print(f"\n\t#### Using file: {temp.name}")
        db = TradingDB(local_config)
        v = db.ensure_version(expected_db_version)
        assert v and v.version == expected_db_version
        with db as conn:
            with conn.cursor() as crs:
                tbls = crs.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                assert set([t[0].upper() for t in tbls]) == expected_tables
        return db

    def test_contract_record(self) -> None:
        probe_tuple = (
            1111,
            ContractRecordStatus.UNCONFIRMED.name,
            12345,
            "SYMBOL",
            "STK",
            "March",
            77.88,
            "RIGHT",
            "MULTI",
            "SMART",
            "USD",
            "L_SYMBOL",
            "NASDAQ",
            "TR_CLASS",
            False,
            "SEC_ID_TYPE",
            "SEC_ID",
            "Something or Other Description",
            "ISSUER_ID",
            "COMBO_LEGS_DESC",
            None,
        )
        probe = ContractRecord(
            str(uuid4()),
            int(datetime.datetime.now().timestamp() * 1000),
            *probe_tuple,
        )
        probe_values = probe.values()

        assert contractCompanion.db_version == 1, f"Incorrect Db Configured {expected_db_version:%d}"
        with self.__local_db__() as db:
            with db.cursor() as crs_inserter:
                tbls = crs_inserter.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                assert set([t[0].upper() for t in tbls]) == expected_tables

                crs_inserter.execute(contractCompanion.value_inserter, probe_values)
            with db.cursor() as crs_reader:
                tbls = crs_reader.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                assert set([t[0].upper() for t in tbls]) == expected_tables
                records = crs_reader.execute(contractCompanion.selector + ";").fetchall()
                assert len(records) == 1, "Should have only one record: {}".format(records)
                assert records[0] == probe_values, "Values should match: \n\t{}\n\t{}".format(records[0], probe_values)
