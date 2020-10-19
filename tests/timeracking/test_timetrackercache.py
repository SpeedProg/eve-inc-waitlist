import unittest
from waitlist.utility.timetracking.timer import TimeTrackerCache
import datetime
from unittest.mock import MagicMock, call
from alchemy_mock.mocking import AlchemyMagicMock, UnifiedAlchemyMagicMock
from waitlist.storage.database import FleetTimeLastTracked


class TimeTrackerCacheTest(unittest.TestCase):


    def test_rejoined_fleet(self):
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock
        fleetmock = MagicMock()
        fleetmock.registrationTime = datetime.datetime.utcnow()-datetime.timedelta(minutes=1)

        # the fleetmember that is in the cache
        fleetmember = MagicMock();
        fleetmember.character_id.return_value = 1
        old_join_datetime = datetime.datetime.utcnow()
        fleetmember.join_datetime.return_value = old_join_datetime

        members = {}
        members[1] = fleetmember

        # the fleetmember that is the same but has new join_datetime
        fleetmember_new = MagicMock()
        fleetmember_new.join_datetime.return_value = old_join_datetime+datetime.timedelta(minutes=1)
        fleetmember_new.character_id.return_value = 1

        cache = TimeTrackerCache(members, datetime.datetime.utcnow()+datetime.timedelta(days=1),
                                 fleetmock)
        self.assertTrue(cache.rejoined_fleet(fleetmember_new), "Failed on rejoined_fleet")

    def test_rejoined_fleet_never_was_in_fleet(self):
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock
        fleetmock = MagicMock()
        fleetmock.registrationTime = datetime.datetime.utcnow()-datetime.timedelta(minutes=1)

        # the fleetmember that is in the cache
        fleetmember = MagicMock();
        fleetmember.character_id.return_value = 1
        old_join_datetime = datetime.datetime.utcnow()
        fleetmember.join_datetime.return_value = old_join_datetime

        members = {}
        members[1] = fleetmember

        # the fleetmember that is the same but has new join_datetime
        fleetmember_new = MagicMock()
        fleetmember_new.join_datetime.return_value = old_join_datetime+datetime.timedelta(minutes=1)
        fleetmember_new.character_id.return_value = 2

        cache = TimeTrackerCache(members, datetime.datetime.utcnow()+datetime.timedelta(days=1),
                                 fleetmock)
        self.assertFalse(cache.rejoined_fleet(fleetmember_new), "Failed on rejoined_fleet for some one who never was in fleet")

    def test_changed_ship_type(self):
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock
        fleetmock = MagicMock()
        fleetmock.registrationTime = datetime.datetime.utcnow()-datetime.timedelta(minutes=1)

        # the fleetmember that is in the cache
        fleetmember = MagicMock();
        fleetmember.character_id.return_value = 1
        fleetmember.ship_type_id.return_value = 2

        members = {}
        members[1] = fleetmember

        # the fleetmember that is the same but has new join_datetime
        fleetmember_new = MagicMock()
        fleetmember_new.character_id.return_value = 1
        fleetmember_new.ship_type_id.return_value = 3

        cache = TimeTrackerCache(members, datetime.datetime.utcnow()+datetime.timedelta(days=1),
                                 fleetmock)
        self.assertTrue(cache.changed_ship_type(fleetmember_new), "Failed to detect ship type change")

    def test_changed_ship_type_no_change(self):
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock
        fleetmock = MagicMock()
        fleetmock.registrationTime = datetime.datetime.utcnow()-datetime.timedelta(minutes=1)

        # the fleetmember that is in the cache
        fleetmember = MagicMock();
        fleetmember.character_id.return_value = 1
        fleetmember.ship_type_id.return_value = 2

        members = {}
        members[1] = fleetmember

        # the fleetmember that is the same but has new join_datetime
        fleetmember_new = MagicMock()
        fleetmember_new.character_id.return_value = 1
        fleetmember_new.ship_type_id.return_value = 2

        cache = TimeTrackerCache(members, datetime.datetime.utcnow()+datetime.timedelta(days=1),
                                 fleetmock)
        self.assertFalse(cache.changed_ship_type(fleetmember_new),
                         "Failed to detect ship type change for some one who did not change")

    def test_changed_ship_type_never_was_in_fleet(self):
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock
        fleetmock = MagicMock()
        fleetmock.registrationTime = datetime.datetime.utcnow()-datetime.timedelta(minutes=1)

        # the fleetmember that is in the cache
        fleetmember = MagicMock();
        fleetmember.character_id.return_value = 1
        fleetmember.ship_type_id.return_value = 2

        members = {}
        members[1] = fleetmember

        # the fleetmember that is the same but has new join_datetime
        fleetmember_new = MagicMock()
        fleetmember_new.character_id.return_value = 2
        fleetmember_new.ship_type_id.return_value = 2

        cache = TimeTrackerCache(members, datetime.datetime.utcnow()+datetime.timedelta(days=1),
                                 fleetmock)
        self.assertFalse(cache.changed_ship_type(fleetmember_new),
                         "Failed to detect ship type change for some one who never was in fleet")

    def test_last_time_tracked(self):
        session_mock = AlchemyMagicMock()
        from waitlist.base import db
        db.session = session_mock
        fleetmock = MagicMock()
        fleetmock.registrationTime = datetime.datetime.utcnow()-datetime.timedelta(minutes=1)

        # the fleetmember that is in the cache
        fleetmember = MagicMock();
        fleetmember.character_id.return_value = 1
        fleetmember.ship_type_id.return_value = 2

        members = {}
        members[1] = fleetmember

        cache = TimeTrackerCache(members, datetime.datetime.utcnow()+datetime.timedelta(days=1),
                                 fleetmock)

        time = datetime.datetime.utcnow()
        cache.update_last_time_tracked(fleetmember, time)
        self.assertEqual(cache.get_last_time_tracked(fleetmember),
                         time,
                         'Failed to check that last time tracked gets set and returned properly')

    def test_load_last_time_tracked(self):
        time = datetime.datetime.utcnow()
        session_mock = UnifiedAlchemyMagicMock(data=[
            (
                [call.query(FleetTimeLastTracked),
                 call.filter(FleetTimeLastTracked.characterID.in_([1]))],
                                  [FleetTimeLastTracked(characterID=1, lastTimeTracked=time)]
            )]
        )
        from waitlist.base import db
        db.session = session_mock

        fleetmock = MagicMock()
        fleetmock.registrationTime = datetime.datetime.utcnow()-datetime.timedelta(minutes=1)

        # the fleetmember that is in the cache
        fleetmember = MagicMock();
        fleetmember.character_id.return_value = 1
        fleetmember.ship_type_id.return_value = 2

        members = {}
        members[1] = fleetmember

        cache = TimeTrackerCache(members, datetime.datetime.utcnow()+datetime.timedelta(days=1),
                                 fleetmock)

        self.assertEqual(cache.get_last_time_tracked(fleetmember),
                         time,
                         'Failed to check that last time tracked gets set and returned properly')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
