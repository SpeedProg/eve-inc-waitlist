import datetime
from waitlist.storage.database import HistoryEntry, Account, Character,\
    HistoryFits, Shipfit, InvType
from waitlist.base import db
from sqlalchemy import and_, or_, func
from typing import Any, Dict, Union, List, Callable, ClassVar
from builtins import classmethod, staticmethod
from _datetime import timedelta


class StatCache(object):
    def __init__(self) -> None:
        self.__data: Dict[str, Any] = {}

    def has_cache_item(self, key: str) -> bool:
        if key not in self.__data:
            return False

        if self.__data[key]['datetime'] < datetime.datetime.utcnow():
            return False
        return True

    def get_cache_item(self, key: str) -> Any:
        if key not in self.__data:
            return None
        return self.__data[key]

    def add_item_to_cache(self, key: str, item: Any) -> None:
        self.__data[key] = item


class StatsManager(object):
    cache: ClassVar[StatCache] = StatCache()
    STAT_ID_APPROVED_DISTINCT_HULL_CHAR = 'a'
    STAT_ID_APPROVED_FITS = 'b'
    STAT_ID_JOINED_FLEET = 'c'

    @classmethod
    def get_distinct_hull_character_stats(
            cls,
            duration: timedelta):
        def query_wrapper(fnc: Callable[[timedelta], Any],
                          duration: timedelta):
            def f():
                return fnc(duration)
            return f

        return cls.__get_query_result(

            ('Approved distinct Hull/Character '
             + 'combinations last ' + str(duration) + ' days'),

            cls.STAT_ID_APPROVED_DISTINCT_HULL_CHAR
            + "_" + str(duration.total_seconds()),

            query_wrapper(
                StatsManager.__query_distinct_hull_character_combinations,
                duration
            ),

            timedelta(seconds=3600),
            lambda row: row[0],
            lambda row: row[1]
        )

    @classmethod
    def get_approved_fits_by_account_stats(
            cls,
            duration: timedelta):
        def query_wrapper(fnc: Callable[[timedelta], Any],
                          duration: timedelta):
            def f():
                return fnc(duration)
            return f

        return cls.__get_query_result(

            ('Approved fits by account during the '
             + 'last ' + str(duration) + ' days'),

            cls.STAT_ID_APPROVED_FITS
            + "_" + str(duration.total_seconds()),

            query_wrapper(
                StatsManager.__query_approved_ships_by_account,
                duration
            ),

            timedelta(seconds=3600),
            lambda row: row[0],
            lambda row: row[1]
        )

    @classmethod
    def get_joined_members_stats(
            cls,
            duration: timedelta):
        def query_wrapper(fnc: Callable[[timedelta], Any],
                          duration: timedelta):
            def f():
                return fnc(duration)
            return f

        return cls.__get_query_result(

            ('Joined Memembers per month'),

            cls.STAT_ID_JOINED_FLEET
            + "_" + str(duration.total_seconds()),

            query_wrapper(
                StatsManager.__query_joined_members,
                duration
            ),

            timedelta(seconds=3600),
            lambda row: str(row[0])+"-"+str(row[1]),
            lambda row: row[2]
        )

    @classmethod
    def __get_query_result(cls, title: str, dataset_id: str,
                           query_func: Callable[[], Any],
                           cache_time: timedelta,
                           xfunc: Callable[[List[Any]], str],
                           yfunc: Callable[[List[Any]], int]
                           ) -> Dict[
                           str, Union[str, List[Union[int, str]]]
                           ]:
        if cls.cache.has_cache_item(dataset_id):
            result = cls.cache.get_cache_item(dataset_id)['data']
        else:
            # we are going to return this
            dbdata = query_func()
            data = {
                'title': title,
                'xnames': [],
                'yvalues': [],
            }
            if dbdata is not None:
                xnames = data['xnames']
                yvalues = data['yvalues']
                for row in dbdata:
                    xnames.append(xfunc(row))
                    yvalues.append(yfunc(row))

            cls.cache.add_item_to_cache(
                dataset_id,
                StatsManager.__create_cache_item(data, cache_time)
            )
            result = data
        return result

    @staticmethod
    def __create_cache_item(data: Any, expire_in: timedelta):
        return {
                'data': data,
                'datetime': (datetime.datetime.utcnow()
                             + expire_in)
                }

    @staticmethod
    def __query_distinct_hull_character_combinations(duration: timedelta):
        """
        Get distinct hull character combinations for the given duration
        SELECT shipType, COUNT(name)
        FROM (
            SELECT DISTINCT invtypes."typeName" AS "shipType", characters.eve_name AS name
            FROM fittings
            JOIN invtypes ON fittings.ship_type = invtypes."typeID"
            JOIN comp_history_fits ON fittings.id = comp_history_fits."fitID"
            JOIN comp_history ON comp_history_fits."historyID" = comp_history."historyID"
            JOIN characters ON comp_history."targetID" = characters.id
            WHERE
             (
             comp_history.action = 'comp_mv_xup_etr'
             OR
             comp_history.action = 'comp_mv_xup_fit'
             )
            AND DATEDIFF(NOW(),comp_history.time) < 30
        ) AS temp
        GROUP BY "shipType"
        ORDER BY COUNT(name) DESC
        LIMIT 15;
        """
        since: datetime = datetime.datetime.utcnow() - duration

        shiptype_name_combinations = db.session\
            .query(InvType.typeName.label('shipType'),
                   Character.eve_name.label('name'))\
            .distinct() \
            .join(Shipfit, InvType.typeID == Shipfit.ship_type) \
            .join(HistoryFits, Shipfit.id == HistoryFits.fitID) \
            .join(HistoryEntry,
                  HistoryFits.historyID == HistoryEntry.historyID) \
            .join(Character, HistoryEntry.targetID == Character.id) \
            .filter(
                and_(
                    or_(
                        HistoryEntry.action == 'comp_mv_xup_etr',
                        HistoryEntry.action == 'comp_mv_xup_fit'
                    ),
                    HistoryEntry.time >= since
                )
            ).subquery('shiptypeNameCombinations')

        return db.session.query(shiptype_name_combinations.c.shipType,
                                func.count(shiptype_name_combinations.c.name))\
            .group_by(shiptype_name_combinations.c.shipType) \
            .order_by(func.count(shiptype_name_combinations.c.name).desc()) \
            .all()

    @staticmethod
    def __query_approved_ships_by_account(duration: timedelta):
        """
        Gets how many fits an account approved
        during the give duration from now
        SELECT name, COUNT(fitid)
        FROM (
            SELECT DISTINCT accounts.username AS name,
             comp_history_fits.id as fitid
            FROM fittings
            JOIN invtypes ON fittings.ship_type = invtypes."typeID"
            JOIN comp_history_fits ON fittings.id = comp_history_fits."fitID"
            JOIN comp_history ON
             comp_history_fits."historyID" = comp_history."historyID"
            JOIN accounts ON comp_history."sourceID" = accounts.id
            JOIN characters ON comp_history."targetID" = characters.id
            WHERE
             (
             comp_history.action = 'comp_mv_xup_etr'
             OR
             comp_history.action = 'comp_mv_xup_fit'
             )
            AND DATEDIFF(NOW(),comp_history.time) < since
        ) AS temp
        GROUP BY name
        ORDER BY COUNT(fitid) DESC
        LIMIT 15;
        """
        since: datetime = datetime.datetime.utcnow() - duration

        fits_flown_by_subquery = db.session.query(
            Account.username.label('name'),
            HistoryFits.id.label('fitid')
            )\
            .join(HistoryEntry, Account.id == HistoryEntry.sourceID) \
            .join(Character, HistoryEntry.targetID == Character.id) \
            .join(HistoryFits,
                  HistoryEntry.historyID == HistoryFits.historyID)\
            .join(Shipfit, HistoryFits.fitID == Shipfit.id) \
            .join(InvType, Shipfit.ship_type == InvType.typeID) \
            .filter(
                and_(
                    or_(
                        HistoryEntry.action == 'comp_mv_xup_etr',
                        HistoryEntry.action == 'comp_mv_xup_fit'
                    ),
                    HistoryEntry.time >= since
                )
            ).subquery("fitsFlownBy")

        return db.session.query(fits_flown_by_subquery.c.name,
                                func.count(fits_flown_by_subquery.c.fitid))\
            .group_by(fits_flown_by_subquery.c.name) \
            .order_by(func.count(fits_flown_by_subquery.c.fitid).desc()) \
            .all()

    @staticmethod
    def __query_joined_members(duration: timedelta):
        """

        """
        since: datetime = datetime.datetime.utcnow() - duration
        joinedSubquery = db.session.query(
            func.year(HistoryEntry.time).label('year'),
            func.month(HistoryEntry.time).label('month'),
            func.day(HistoryEntry.time).label('day'),
            HistoryEntry.targetID.label('target'),
            )\
            .filter(
                and_(
                    HistoryEntry.action == HistoryEntry.EVENT_AUTO_RM_PL,
                    HistoryEntry.time >= since
                )
            ).distinct().subquery("joinedFleet")
        return db.session.query(joinedSubquery.c.year,
                         joinedSubquery.c.month,
                         func.count(joinedSubquery.c.target)
        ).group_by(
            joinedSubquery.c.year,
             joinedSubquery.c.month
        ).all();
"""
        return db.session.query(
            func.year(HistoryEntry.time),
            func.month(HistoryEntry.time),
            func.count(HistoryEntry.historyID)
            )\
            .filter(
                and_(
                    HistoryEntry.action == HistoryEntry.EVENT_AUTO_RM_PL,
                    HistoryEntry.time >= since
                )
            )\
            .group_by(func.year(HistoryEntry.time), func.month(HistoryEntry.time))\
            .all()
"""
