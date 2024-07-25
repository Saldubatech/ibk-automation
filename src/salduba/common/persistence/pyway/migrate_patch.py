import os
from typing import List

from pyway.configfile import ConfigFile  # type: ignore
from pyway.dbms.database import factory  # type: ignore
from pyway.errors import MIGRATIONS_NOT_FOUND  # type: ignore
from pyway.helpers import Utils  # type: ignore
from pyway.helpers import bcolors  # pyright: ignore
from pyway.migration import Migration  # type: ignore


class Migrate():

    def __init__(self, args: ConfigFile) -> None:
        self._db = factory(args.database_type)(args)
        self._is_sqlite = True if args.database_type == 'sqlite' else False
        self.migration_dir = args.database_migration_dir
        self.args = args

    def run(self) -> str:
        output = ''
        migrations_to_be_executed = self._get_migration_files_to_be_executed()  # pyright: ignore
        if not migrations_to_be_executed:
            output += Utils.color("Nothing to do\n", bcolors.FAIL)
            return output

        for migration in migrations_to_be_executed:  # pyright: ignore
            output += Utils.color(f"Migrating --> {migration.name}\n", bcolors.OKBLUE)  # pyright: ignore
            try:
                with open(os.path.join(os.getcwd(),
                          self.migration_dir, migration.name), "r", encoding='utf-8') as sqlfile:  # pyright: ignore
                    if self._is_sqlite:
                      all_stmts = sqlfile.read()
                      for stmt in all_stmts.split(";"):
                        self._db.execute(stmt)
                    else:
                      self._db.execute(sqlfile.read())
                self._db.upgrade_version(migration)
                output += Utils.color(f"{migration.name} SUCCESS\n", bcolors.OKBLUE)  # pyright: ignore
            except Exception as error:
                raise RuntimeError(error)
        return output

    def _get_migration_files_to_be_executed(self) -> List:  # type: ignore
        all_local_migrations = self._get_all_local_migrations()  # pyright: ignore
        all_db_migrations = Migration.from_list(self._db.get_all_schema_migrations())

        if all_db_migrations and not all_local_migrations:
            raise RuntimeError(MIGRATIONS_NOT_FOUND % self.migration_dir)
        return Utils.subtract(all_local_migrations, all_db_migrations)  # type: ignore

    def _get_all_local_migrations(self) -> List:  # type: ignore
        local_files = Utils.get_local_files(self.migration_dir)
        if not local_files:
            return []  # pyright: ignore
        migrations = [Migration.from_name(local_file, self.migration_dir) for local_file in local_files]
        return Utils.sort_migrations_list(migrations)  # type: ignore
