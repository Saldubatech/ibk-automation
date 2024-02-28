# -*- coding: utf-8 -*-

import unittest
import tempfile

from salduba.ib_tws_proxy.backing_db.db import TradingDB, DbConfig


class TestDb(unittest.TestCase):
    """Test Basic DB Access"""
    config = DbConfig(
        {
            'path': 'tests/resources/test_db.db',
            'schemas': 'salduba/ib_tws_proxy/backing_db/schema',
            'seed_data': 'salduba/ib_tws_proxy/backing_db/seed-data',
            'expected_version': "0",
            'target_version': "1",
            'version_date': "2024-02-01 00:00:00.000"
        }
    )

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)  # type: ignore
        self.db = TradingDB(TestDb.config)

    def test_db_connection(self) -> None:
        with self.db as db:
            assert db.conn
            assert db.connection_depth == 1
        assert self.db.connection_depth == 0
        assert not self.db.conn

    def __local_db__(self) -> TradingDB:
        temp = tempfile.NamedTemporaryFile()
        temp.close()
        local_config = DbConfig({
            'path': temp.name,
            'schemas': 'salduba/ib_tws_proxy/backing_db/schema',
            'seed_data': 'salduba/ib_tws_proxy/backing_db/seed-data',
            'expected_version': "0",
            'target_version': "1",
            'version_date': "2024-02-01 00:00:00.000"
            }
        )
        return TradingDB(local_config)

    def test_0_version(self) -> None:
        with self.__local_db__() as local_db:
            assert not local_db.version()
            assert not local_db.validate(0)
            assert not local_db.ensure_version(0, True)

    def test_ensure_version(self) -> None:
        with self.__local_db__() as local_db:
            v = local_db.ensure_version(1)
            assert v and v.version == 1, f"Version is {v}"


if __name__ == '__main__':
    unittest.main()
