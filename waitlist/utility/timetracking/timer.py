from typing import KeysView, Dict
from datetime import datetime, timedelta
import logging
from threading import Timer, Lock
from ..fleet import member_info
from ...storage.database import CrestFleet, FleetTime, Character, FleetTimeLastTracked, FleetTimeByHull
from ...base import db
from ..swagger.eve.fleet.models import FleetMember


logger = logging.getLogger(__name__)


class TimeTrackerCache:
    def __init__(self, members: Dict[int, FleetMember], expires: datetime,
                 fleet: CrestFleet):
        self.members: Dict[int, FleetMember] = members
        self.expires: datetime = expires
        self.last_time_tracked: Dict[int, datetime] = {}
        self.fleet_registration_time: datetime = fleet.registrationTime

    def rejoined_fleet(self, member: FleetMember) -> bool:
        '''Check if this member rejoined Fleet'''
        return self.members[member.character_id()].join_datetime() < member.join_datetime()

    def changed_ship_type(self, member: FleetMember) -> bool:
        '''Check if this member changed his hull type'''
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
        if member.character_id() in self.last_time_tracked:
            db.session.update(FleetTimeLastTracked)\
                .where(FleetTimeLastTracked.characterID == member.character_id())\
                .values(lastTimeTracked=time)
        else:
            ftlt: FleetTimeLastTracked = FleetTimeLastTracked(
                characterID=member.character_id(),
                lastTimeTracked=time)
            db.session.add(ftlt)
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
            for fleet_id in self.cache.keys():
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
                    fleet_new_data: Dict[int, FleetMember] = member_info.get_fleet_members(fleet_id, fleet.comp)
                    fleet_expires = member_info.get_expires(fleet_id)
                    tt_data: TimeTrackerCache = self.cache[fleet_id]
                    # if we get stale data, because e.g. we have no valid api key
                    # just skip this fleet
                    if fleet_expires == tt_data.expires:
                        logger.debug('Skipping fleet with id=%s because cache data is stale', fleet_id)
                        continue
                    # find members not in new data (they left the fleet)
                    # or members that have newer join time (they rejoined)
                    # or members that have have a different hull (they switched ship)
                    for member_id in tt_data.members.keys():
                        logger.debug('Checking memeber with character_id=%s', member_id)
                        if member_id in fleet_new_data:
                            logger.debug('Member is still in fleet')
                            # now check his join time, if it changed he rejoined
                            # and we need to add his time from before
                            # so that time does not disappear
                            if tt_data.rejoined_fleet(fleet_new_data[member_id]):
                                logger.debug('Member rejoined fleet since last check')
                                self.register_member_time(
                                    fleet_id,
                                    tt_data.members[member_id],
                                    tt_data.expires,
                                    tt_data)
                            # we must only track if he did not rejoin
                            elif tt_data.changed_ship_type(fleet_new_data[member_id]):
                                logger.debug('Member %s changed hull', tt_data.members[member_id].character_id())
                                self.register_member_time(
                                    fleet_id,
                                    tt_data.members[member_id],
                                    tt_data.expires,
                                    tt_data)
                        else:  # he left fleet
                            logger.debug('Member left fleet')
                            self.register_member_time(fleet_id,
                                                      tt_data.members[member_id],
                                                      tt_data.expires,
                                                      tt_data)
                    # we don't need to care about new members,
                    # because we handle all members when they leave,
                    # because only then we know the duration they stayed for

                    # now we can replace the data
                    self.cache[fleet_id].members = fleet_new_data.copy()
                    self.cache[fleet_id].expires = fleet_expires

            # add new fleets to cache
            for fleet_id in fleet_ids:
                if fleet_id not in self.cache:
                    logger.info('Adding new fleet with fleet_id=%s to cache', fleet_id)
                    fleet: CrestFleet = db.session.query(CrestFleet).get(fleet_id)
                    member_data = member_info.get_fleet_members(fleet_id, fleet.comp)
                    expires_data = member_info.get_expires(fleet_id)
                    self.cache[fleet_id] = TimeTrackerCache(member_data, expires_data, fleet)

            db.session.commit()
            db.session.remove()

            if not self.stopped:
                logger.info('Registering new timer')
                self.timer = Timer(300, self.check_fleets)
                self.timer.start()
            else:
                logger.info('Not setting up new timer, because Tracker is stopped')
        except Exception as e:
            logger.exception('Failed')

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
        self.state_lock.acquire(True)
        logger.info('Starting time tracking')
        if not self.stopped:
            self.state_lock.release()
            logger.info('Time tracking was already running')
            return
        self.stopped = False
        self.cache = {}
        #  just set the first soon
        self.timer = Timer(1, self.check_fleets)
        self.timer.start()
        self.state_lock.release()

    def stop_tracking(self) -> None:
        self.state_lock.acquire(True)
        logger.info('Stopping time tracking')
        if self.stopped:
            logger.info('Time tracking was already stopped')
            self.state_lock.release()
            return
        self.stopped = True
        if self.timer is not None:
            self.timer.cancel()
        else:
            logger.info('Timer was not set, can not cancel')
        self.state_lock.release()

    def register_fleet_time(self, fleet_id: int, fleet_cache: TimeTrackerCache) -> None:
        for member_id in fleet_cache.members:
            self.register_member_time(fleet_id, fleet_cache.members[member_id],
                                      fleet_cache.expires, fleet_cache)

    def register_member_time(self, fleet_id: int, member: FleetMember,
                             until: datetime, cache: TimeTrackerCache):
        join_datetime = member.join_datetime()
        if join_datetime.tzinfo is not None:
            join_datetime = join_datetime.replace(tzinfo=None) - join_datetime.utcoffset()

        duration_in_fleet: timedelta = until - max(join_datetime, cache.get_last_time_tracked(member))
        if logger.isEnabledFor(logging.DEBUG):
            character: Character = db.session.query(Character).get(member.character_id())

            logger.debug('Registering %s seconds for member with name=%s character_id=%s hull=%s',
                         duration_in_fleet.total_seconds(),
                         character.get_eve_name(),
                         member.character_id(),
                         member.ship_type_id())
        if db.session.query(FleetTime).filter_by(characterID=member.character_id()).count() <= 0:
            # we need to create entries
            ft = FleetTime(characterID=member.character_id(),
                           duration=duration_in_fleet.total_seconds())
            db.session.add(ft)
        else:
            db.session.query(FleetTime).\
                filter_by(characterID=member.character_id()).\
                update({'duration': FleetTime.duration + duration_in_fleet.total_seconds()})

        if db.session.query(FleetTimeByHull).filter_by(characterID=member.character_id(), hullType=member.ship_type_id()).count() <= 0:
            ftbh = FleetTimeByHull(
                characterID=member.character_id(),
                hullType=member.ship_type_id(),
                duration=duration_in_fleet.total_seconds()
            )
            db.session.add(ftbh)
        else:
            db.session.query(FleetTimeByHull)\
                .filter_by(characterID=member.character_id(), hullType=member.ship_type_id())\
                .update({'duration': FleetTimeByHull.duration + duration_in_fleet.total_seconds()})
        cache.update_last_time_tracked(member, until)
