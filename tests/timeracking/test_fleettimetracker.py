import unittest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock, AlchemyMagicMock, mock
from waitlist.storage.database import FleetTimeByDayHull,\
    CrestFleet
import datetime
from unittest.mock import MagicMock
from waitlist.utility.swagger.eve.fleet.models import FleetMember


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fleet_removed(self):
        from waitlist.utility.timetracking.timer import FleetTimeTracker
        fleetTimeTracker = FleetTimeTracker()

        fleetCache = MagicMock()

        cacheDictMock = MagicMock()
        cacheDictMock.__getitem__.return_value = fleetCache
        cacheDictMock.get.return_value = fleetCache
        fleetTimeTracker.register_fleet_time = MagicMock(return_value=None)
        fleetTimeTracker.cache = cacheDictMock

        fleetTimeTracker.fleet_removed(1, datetime.datetime.utcnow())

        # check the fleet was sent for time registration
        fleetTimeTracker.register_fleet_time.assert_called_once_with(1, fleetCache)
        # check the fleet was removed from the cache
        cacheDictMock.__delitem__.assert_called_once_with(1)

    def test_register_fleet_time(self):
        from waitlist.utility.timetracking.timer import FleetTimeTracker
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock

        member_join_time = datetime.datetime.utcnow()
        membersRegister = {}
        member1 = MagicMock()
        member1.join_datetime.return_value = member_join_time
        member2 = MagicMock()
        member2.join_datetime.return_value = member_join_time

        membersRegister[1] = member1
        membersRegister[2] = member2

        fleetCache = MagicMock()
        fleetCache.get_last_time_tracked.return_value = member_join_time - datetime.timedelta(minutes=5)

        membersMock = MagicMock()

        def get_item(key):
            return membersRegister[key]

        def get_keys():
            return membersRegister.keys()

        membersMock.__getitem__.side_effect = get_item
        membersMock.keys.side_effect = get_keys
        membersMock.__iter__.side_effect = membersRegister.__iter__

        fleetExpires = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        fleetCache.members = membersMock
        fleetCache.expires = fleetExpires

        tracker = FleetTimeTracker()
        # make sure there is no sideeffects from thse calls
        tracker.register_member_time = MagicMock()
        tracker.register_fleet_time(1, fleetCache)

        # we iterated over all members
        membersMock.__getitem__.assert_any_call(1)
        membersMock.__getitem__.assert_any_call(2)
        tracker.register_member_time.assert_any_call(1, member1, fleetExpires, fleetCache)
        tracker.register_member_time.assert_any_call(1, member2, fleetExpires, fleetCache)

    def test_register_member_time_daychange(self):
        from waitlist.utility.timetracking.timer import TimeTrackerCache, FleetTimeTracker
        # fake fleet for registartion time
        fleet = MagicMock()
        fleet.registrationTime = datetime.datetime(2020, 12, 6, 11, 0, 0)
        # fleetmembers
        member01_join_time = datetime.datetime(2020, 12, 6, 11, 1, 0)
        fleetMember01 = self.get_basic_fleetmember(member01_join_time, 1)
        # member02_join_time = datetime.datetime(2020, 12, 6, 12, 0, 0)
        # fleetMember02 = self.get_basic_fleetmember(member02_join_time, 2)

        # lets setup our timetracker cache
        ttc = TimeTrackerCache(
            {1: fleetMember01},
            datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            fleet)
        ttc.update_last_time_tracked = MagicMock()
        ftt = FleetTimeTracker()
        ftt.cache[1] = ttc

        # change the methods which get called to intercept them
        ftt.register_time = MagicMock()
        # character_id: int, day: date, hull_type: int, duration: timedelta

        until_time = datetime.datetime(2020, 12, 7, 1, 0, 0)
        # lets put the until to an other day
        ftt.register_member_time(1, fleetMember01, until_time, ttc)

        duration01 = datetime.datetime.combine(member01_join_time, datetime.datetime.max.time()) - member01_join_time
        duration02 = (until_time - member01_join_time) - duration01
        ftt.register_time.assert_any_call(1, member01_join_time.date(), 1, duration01)
        ftt.register_time.assert_any_call(1, until_time.date(), 1, duration02)
        ttc.update_last_time_tracked.assert_called_once_with(fleetMember01, until_time)

    def test_register_time(self):
        from waitlist.utility.timetracking.timer import TimeTrackerCache, FleetTimeTracker
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock

        # mock the session so update querys show there is no entry
        session_mock.query.return_value.filter_by.return_value.update.return_value = 0

        # fake fleet for registartion time
        fleet = MagicMock()
        fleet.registrationTime = datetime.datetime(2020, 12, 6, 11, 0, 0)
        # fleetmembers
        member01_join_time = datetime.datetime(2020, 12, 6, 11, 1, 0)
        fleetMember01 = self.get_basic_fleetmember(member01_join_time, 1)
        # member02_join_time = datetime.datetime(2020, 12, 6, 12, 0, 0)
        # fleetMember02 = self.get_basic_fleetmember(member02_join_time, 2)

        # lets setup our timetracker cache
        ttc = TimeTrackerCache(
            {1: fleetMember01},
            datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            fleet)
        ftt = FleetTimeTracker()
        ftt.cache[1] = ttc
        ftt.register_time(1, member01_join_time.date(), 1, datetime.timedelta(hours=2, minutes=48))

        session_mock.add.assert_called()

    def test_register_time_already_has_entry(self):
        from waitlist.utility.timetracking.timer import TimeTrackerCache, FleetTimeTracker
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock
        # fake fleet for registartion time
        fleet = MagicMock()
        fleet.registrationTime = datetime.datetime(2020, 12, 6, 11, 0, 0)
        # fleetmembers
        member01_join_time = datetime.datetime(2020, 12, 6, 11, 1, 0)
        fleetMember01 = self.get_basic_fleetmember(member01_join_time, 1)
        # member02_join_time = datetime.datetime(2020, 12, 6, 12, 0, 0)
        # fleetMember02 = self.get_basic_fleetmember(member02_join_time, 2)

        # lets setup our timetracker cache
        ttc = TimeTrackerCache(
            {1: fleetMember01},
            datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            fleet)
        ftt = FleetTimeTracker()
        ftt.cache[1] = ttc

        duration = datetime.timedelta(hours=2, minutes=48)
        ftt.register_time(1, member01_join_time.date(), 1, duration)

        # mock the update so it thinks there is an entry
        session_mock.query.return_value.filter_by.return_value.update.return_value = 1
        session_mock.query.return_value.filter_by.return_value.update.assert_called_with({'duration': FleetTimeByDayHull.duration + duration.total_seconds()})
        # make sure it doesn't try to add an entrie, if there is one
        session_mock.add.assert_not_called()

    def test_check_fleets_left(self):
        session_mock = UnifiedAlchemyMagicMock(data=[
            (
                [mock.call.query(CrestFleet),
                 mock.call.filter(CrestFleet.fleetID == 1)],
                [CrestFleet(fleetID=1)]
            )
        ])
        from waitlist.base import db
        db.session = session_mock

        # here we want to mock fleet_info to see if it properly works with it
        info_mock = MagicMock()
        from waitlist.utility import fleet
        fleet.member_info = info_mock
        from waitlist.utility.timetracking.timer import FleetTimeTracker

        member01 = self.get_basic_fleetmember(datetime.datetime(2020, 12, 6, 1, 0, 0), 1)
        member02 = self.get_basic_fleetmember(datetime.datetime(2020, 12, 6, 1, 0, 0), 2)
        member03 = self.get_basic_fleetmember(datetime.datetime(2020, 12, 6, 1, 0, 0), 3)
        lastCacheTime = datetime.datetime(2020, 12, 6, 1, 0, 0)

        fleetInfoDict = {1: {1: member01, 2: member02, 3: member03}}

        info_mock.get_fleet_ids.side_effect = lambda: fleetInfoDict.keys()
        info_mock.get_fleet_members.side_effect = lambda fid, _: fleetInfoDict[fid].copy()
        info_mock.get_expires.return_value = lastCacheTime

        ftt = FleetTimeTracker()
        ftt.register_member_time = MagicMock()
        # make sure it does actually run
        ftt.stopped = False

        ftt.check_fleets() # this should now go through those 3 members
        # we need to stop the timer for the unittest
        ftt.timer.cancel()
        # now one member leaves
        del fleetInfoDict[1][2]
        # also make sure we have a new cachetime
        info_mock.get_expires.return_value = datetime.datetime(2020, 12, 6, 1, 0, 5)

        ftt.check_fleets()
        ftt.timer.cancel()
        # now the id 2 members time should have been submitted
        ftt.register_member_time.assert_called_once_with(1, member02, lastCacheTime, ftt.cache[1])

    def get_basic_fleetmember(self, join_time: datetime.datetime, character_id: int) -> FleetMember:
        # join_time gets access in a weird way, it acces .v on it
        join_time_holder = MagicMock()
        join_time_holder.v = join_time
        baseData = {'character_id': character_id, 'join_time': join_time_holder,
                    'role': 'a', 'role_name': 'a', 'ship_type_id': 1,
                    'solar_system_id': 1, 'squad_id': 1, 'station_id': 1,
                    'takes_fleet_warp': False, 'wing_id': 1}
        return FleetMember(baseData)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
