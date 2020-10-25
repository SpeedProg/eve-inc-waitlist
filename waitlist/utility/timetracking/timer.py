from typing import KeysView, Dict
from datetime import datetime, timedelta, date
import logging
from threading import Timer, Lock
from ..fleet import member_info
from ...storage.database import CrestFleet, FleetTime, Character, FleetTimeLastTracked, FleetTimeByHull, FleetTimeByDayHull
from ...base import db
from ..swagger.eve.fleet.models import FleetMember
from ..eve_id_utils import get_character_by_id


logger = logging.getLogger(__name__)


class TimeTrackerCache:
    def __init__(self, members: Dict[int, FleetMember], expires: datetime,
                 fleet: CrestFleet):
        self.members: Dict[int, FleetMember] = members
        self.expires: datetime = expires
        self.last_time_tracked: Dict[int, datetime] = {}
        self.fleet_registration_time: datetime = fleet.registrationTime
        self.__load_last_time_tracked()

    def rejoined_fleet(self, member: FleetMember) -> bool:
        '''Check if this member rejoined Fleet'''
        if member.character_id() not in self.members:
            return False
        return self.members[member.character_id()].join_datetime() < member.join_datetime()

    def changed_ship_type(self, member: FleetMember) -> bool:
        '''Check if this member changed his hull type'''
        if member.character_id() not in self.members:
            return False
        return self.members[member.character_id()].ship_type_id() != member.ship_type_id()

    def get_last_time_tracked(self, member: FleetMember) -> datetime:
        if member.character_id() in self.last_time_tracked:
            return self.last_time_tracked[member.character_id()]
        return self.fleet_registration_time

    def __load_last_time_tracked(self) -> None:
        member_ids = list(self.members.keys())
        data_query = db.session.query(FleetTimeLastTracked)\
            .filter(FleetTimeLastTracked.characterID.in_(member_ids))
        for track_info in data_query:
            self.last_time_tracked[track_info.characterID] = track_info.lastTimeTracked

    def update_last_time_tracked(self, member: FleetMember, time: datetime) -> None:
        rowcount = db.session.query(FleetTimeLastTracked)\
            .filter_by(characterID=member.character_id())\
            .update({'lastTimeTracked': time})

        if rowcount != 1:
            ftlt: FleetTimeLastTracked = FleetTimeLastTracked(
                characterID=member.character_id(),
                lastTimeTracked=time)
            db.session.add(ftlt)
            db.session.commit()

        self.last_time_tracked[member.character_id()] = time


class FleetTimeTracker:
    def __init__(self):
        self.cache: Dict[int, TimeTrackerCache] = {}
        self.timer = None
        self.stopped = True
        self.state_lock = Lock()

    def check_fleets(self):
        try:
            if self.stopped:
                logger.info('Not running because tracker is stopped')
                return
            logger.info('check_fleets executing')
            fleet_ids: KeysView = member_info.get_fleet_ids()
            # lets check if any fleets are gone that we still have data of
            for fleet_id in list(self.cache.keys()):
                logger.debug('Checking fleet_id=%s if it still exists', fleet_id)
                if fleet_id not in fleet_ids:
                    logger.info('Fleet with id=%s is not in cache anymore, removing', fleet_id)
                    # the fleet disappeared register remaining mebers time
                    self.register_fleet_time(fleet_id, self.cache[fleet_id])
                    del self.cache[fleet_id]

            for fleet_id in self.cache.keys():
                logger.debug('Checking members in fleet with id=%s', fleet_id)
                if fleet_id in fleet_ids:
                    # these ones we need to check for missing members, because they left the fleet
                    # we also need to check all none missing members if their fleet join time maybe changed because if it did, it means they left and rejoined between the last check and now
                    fleet: CrestFleet = db.session.query(CrestFleet).get(fleet_id)
                    fleet_new_data: Dict[int, FleetMember] = None if fleet.comp is None else member_info.get_fleet_members(fleet_id, fleet.comp)
                    fleet_expires = member_info.get_expires(fleet_id)
                    tt_data: TimeTrackerCache = self.cache[fleet_id]
                    # if we get stale data, because e.g. we have no valid api key
                    # just skip this fleet
                    if fleet_new_data is None:
                        logger.info('Fleet with id=%s is not in cache anymore also its key still exists in database, removing', fleet_id)
                        # the fleet disappeared register remaining mebers time
                        self.register_fleet_time(fleet_id, self.cache[fleet_id])
                        del self.cache[fleet_id]
                        continue

                    if fleet_expires == tt_data.expires:
                        logger.debug('Skipping fleet with id=%s because cache data is stale', fleet_id)
                        continue
                    # find members not in new data (they left the fleet)
                    # or members that have newer join time (they rejoined)
                    # or members that have have a different hull (they switched ship)
                    for member_id in tt_data.members.keys():
                        if member_id in fleet_new_data:
                            # now check his join time, if it changed he rejoined
                            # and we need to add his time from before
                            # so that time does not disappear
                            if tt_data.rejoined_fleet(fleet_new_data[member_id]):
                                logger.debug('Member character_id=%s rejoined fleet since last check', member_id)
                                self.register_member_time(
                                    fleet_id,
                                    tt_data.members[member_id],
                                    tt_data.expires,
                                    tt_data)
                            # we must only track if he did not rejoin
                            elif tt_data.changed_ship_type(fleet_new_data[member_id]):
                                logger.debug('Member character_id=%s changed hull', member_id)
                                self.register_member_time(
                                    fleet_id,
                                    tt_data.members[member_id],
                                    tt_data.expires,
                                    tt_data)
                            else:
                                logger.debug('Member character_id=%s is still in fleet', member_id)
                        else:  # he left fleet
                            logger.debug('Member character_id=%s left fleet', member_id)
                            self.register_member_time(fleet_id,
                                                      tt_data.members[member_id],
                                                      tt_data.expires,
                                                      tt_data)
                    # we don't need to care about new members,
                    # because we handle all members when they leave,
                    # because only then we know the duration they stayed for
                    if logger.isEnabledFor(logging.DEBUG):
                        for member_id in fleet_new_data.keys():
                            if member_id not in tt_data.members:
                                logger.debug('Memeber character_id=%s joined fleet', member_id)

                    # now we can replace the data
                    self.cache[fleet_id].members = fleet_new_data.copy()
                    self.cache[fleet_id].expires = fleet_expires

            # add new fleets to cache
            for fleet_id in fleet_ids:
                if fleet_id not in self.cache:
                    logger.info('Adding new fleet with fleet_id=%s to cache', fleet_id)
                    fleet: CrestFleet = db.session.query(CrestFleet).get(fleet_id)
                    if fleet.comp is None:
                        logger.info('Skipping fleet with id=%s because we do not have a fleet comp')
                        continue
                    member_data = member_info.get_fleet_members(fleet_id, fleet.comp)
                    if member_data is not None:
                        logger.info('Fleet with fleet_id=%s does not have data', fleet_id)
                        expires_data = member_info.get_expires(fleet_id)
                        self.cache[fleet_id] = TimeTrackerCache(member_data, expires_data, fleet)

            db.session.commit()

        except Exception as e:
            logger.exception('Failed')
        finally:
            db.session.remove()

            with self.state_lock:
                if not self.stopped:
                    logger.info('Registering new timer')
                    self.timer = Timer(300, self.check_fleets)
                    self.timer.start()
                else:
                    logger.info('Not setting up new timer, because Tracker is stopped')

    def fleet_removed(self, fleet_id: int,
                      registration_time: datetime) -> None:
        # add all the time of remaining member, then delete from cache
        logger.info('Fleet id=%s was removed', fleet_id)
        fleet = self.cache.get(fleet_id)
        if fleet is None:
            logger.info('Fleet id=%s was attempted to be removed but it wasn\'t found in the cache', fleet_id)
            return

        self.register_fleet_time(fleet_id, fleet)
        del self.cache[fleet_id]

    def start_tracking(self) -> None:
        '''Start the tracking if it isn't already started'''
        with self.state_lock:
            logger.info('Starting time tracking')
            if not self.stopped:
                logger.info('Time tracking was already running')
                return
            self.stopped = False
            self.cache = {}
            #  just set the first soon
            self.timer = Timer(1, self.check_fleets)
            self.timer.start()

    def stop_tracking(self) -> None:
        '''Stop the tracking if it is running'''
        with self.state_lock:
            logger.info('Stopping time tracking')
            if self.stopped:
                logger.info('Time tracking was already stopped')
                return
            self.stopped = True
            if self.timer is not None:
                self.timer.cancel()
            else:
                logger.info('Timer was not set, can not cancel')

    def register_fleet_time(self, fleet_id: int, fleet_cache: TimeTrackerCache) -> None:
        '''Register the fleet time for every member in the fleet cache'''
        for member_id in fleet_cache.members:
            self.register_member_time(fleet_id, fleet_cache.members[member_id],
                                      fleet_cache.expires, fleet_cache)

    def register_member_time(self, fleet_id: int, member: FleetMember,
                             until: datetime, cache: TimeTrackerCache):
        join_datetime = member.join_datetime()
        if join_datetime.tzinfo is not None:
            join_datetime = join_datetime.replace(tzinfo=None) - join_datetime.utcoffset()

        interval_start = max(join_datetime, cache.get_last_time_tracked(member))
        interval_end = until
        try:
            if interval_start.date() == interval_end.date():
                self.register_time(member.character_id(), interval_end.date(),
                                   member.ship_type_id(), interval_end-interval_start)
            else:
                # seems we are starting on a different day then ending it
                # lets count the time until midnight first
                duration_to_daychange = datetime.combine(interval_start, datetime.max.time()) - interval_start
                full_duration = interval_end - interval_start
                self.register_time(member.character_id(), interval_start.date(),
                               member.ship_type_id(),
                                   duration_to_daychange)
                self.register_time(member.character_id(), interval_end.date(),
                                   member.ship_type_id(),
                                   full_duration-duration_to_daychange)

            cache.update_last_time_tracked(member, until)
        except Exception:
            logger.exception("Failed to register fleet time for %s", member.character_id(), exc_info=True)

    def register_time(self, character_id: int, day: date, hull_type: int, duration: timedelta) -> None:
        # this makes sure we have the character in databse so we can actually link the record to it
        character: Character = get_character_by_id(character_id)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Registering %s seconds for member with name=%s character_id=%s hull=%s day=%s',
                         duration.total_seconds(),
                         character.get_eve_name(),
                         character_id,
                         hull_type,
                         day)
        rowcount = db.session.query(FleetTime)\
            .filter_by(characterID=character_id)\
            .update({'duration': FleetTime.duration + duration.total_seconds()})
        if rowcount == 0:
            # we need to create entries
            ft = FleetTime(characterID=character_id,
                           duration=duration.total_seconds())
            db.session.add(ft)

        rowcount = db.session.query(FleetTimeByHull)\
            .filter_by(characterID=character_id, hullType=hull_type)\
            .update({'duration': FleetTimeByHull.duration + duration.total_seconds()})
        if rowcount == 0:
            ftbh = FleetTimeByHull(
                characterID=character_id,
                hullType=hull_type,
                duration=duration.total_seconds()
            )
            db.session.add(ftbh)

        rowcount = db.session.query(FleetTimeByDayHull)\
            .filter_by(characterID=character_id, hullType=hull_type, day=day)\
            .update({'duration': FleetTimeByDayHull.duration + duration.total_seconds()})

        if rowcount == 0:
            ftbdh = FleetTimeByDayHull(
                characterID=character_id,
                hullType=hull_type,
                day=day,
                duration=duration.total_seconds())
            db.session.add(ftbdh)
