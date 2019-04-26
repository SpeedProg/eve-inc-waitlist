import logging
from decimal import Decimal
from typing import Optional, List, Tuple
from waitlist.storage.database import Waitlist, ShipCheckCollection, ShipCheck,\
    InvType, InvGroup, MarketGroup, WaitlistGroup
from waitlist.base import db
from waitlist.storage import modules
from waitlist.utility.constants import check_types



def add_default_sorting(collection: ShipCheckCollection, logi_wl, dps_wl, sniper_wl):

    #  how old WTM sorting worked was to first sort out T2 logi ships :>
    check = ShipCheck(
        checkName = 'SortOutLogiHulls',
        checkTargetID = logi_wl.id,
        checkType = check_types.SHIP_CHECK_TYPEID,
        order = 0,
        modifier = Decimal('1.00'),
        checkTag = 'logi'
    )

    collection.checks.append(check)

    for k, v in modules.logi_ships.items():
        inv_type: InvType = db.session.query(InvType).get(k)
        if inv_type is None:
            print('ERROR NONE', inv_type)

        check.ids.append(inv_type)

    # check dps weapons
    check = ShipCheck(
        checkName = 'SortToDpsByWeapon',
        checkTargetID=dps_wl.id,
        checkType = check_types.MODULE_CHECK_TYPEID,
        order = 1,
        modifier = Decimal('1.00'),
        checkTag = 'dps'
    )

    collection.checks.append(check)

    for k, v in modules.dps_weapons.items():
        inv_type = db.session.query(InvType).get(k)
        if inv_type is None:
            print('ERROR NONE', inv_type)

        check.ids.append(inv_type)

    # check sniper weapons
    check = ShipCheck(
        checkName = 'SortToSniperByWeapon',
        checkTargetID = sniper_wl.id,
        checkType = check_types.MODULE_CHECK_TYPEID,
        order = 1,
        modifier = Decimal('1.00'),
        checkTag = 'sniper'
    )
    collection.checks.append(check)

    for k, v in modules.sniper_weapons.items():
        inv_type = db.session.query(InvType).get(k)
        if inv_type is None:
            print('ERROR NONE', inv_type)

        check.ids.append(inv_type)

    # check sniper by market group
    check = ShipCheck(
        checkName = 'SortToSniperByWeaponMarketGroup',
        checkTargetID = sniper_wl.id,
        checkType = check_types.MODULE_CHECK_MARKETGROUP,
        order = 2,
        modifier = Decimal('1.00'),
        checkTag = 'sniper'
    )
    collection.checks.append(check)

    for k, v in modules.weapongroups['sniper'].items():
        grp = db.session.query(MarketGroup).get(v)
        if grp is None:
            print('ERROR NONE sniper weapon grps', v)
        check.ids.append(grp)

    # check dps by market group
    check = ShipCheck(
        checkName = 'SortToDpsByWeaponMarketGroup',
        checkTargetID = dps_wl.id,
        checkType = check_types.MODULE_CHECK_MARKETGROUP,
        order = 2,
        modifier = Decimal('1.00'),
        checkTag = 'sniper'
    )
    collection.checks.append(check)

    for k, v in modules.weapongroups['dps'].items():
        if v == 2432: # skip Entropic Disintigrators
            continue
        grp = db.session.query(MarketGroup).get(v)
        if grp is None:
            print('ERROR NONE dps weapongroups', v)
        check.ids.append(grp)

    # special rule for entropic disintigrators because it needs a higher modifier
    check = ShipCheck(
        checkName = 'SortToSniperEntropicDisintigrators',
        checkTargetID = sniper_wl.id,
        checkType = check_types.MODULE_CHECK_MARKETGROUP,
        order = 2,
        modifier = Decimal('4.00'),
        checkTag = 'sniper'
    )
    collection.checks.append(check)
    check.ids.append(db.session.query(MarketGroup).get(2432))

    # check dps by ship_type
    check = ShipCheck(
        checkName = 'SortToDpsByShipType',
        checkTargetID = dps_wl.id,
        checkType = check_types.SHIP_CHECK_TYPEID,
        order = 3,
        modifier = Decimal('1.00'),
        checkTag = 'dps'
    )
    collection.checks.append(check)

    for k, v in modules.dps_ships.items():
        inv_type = db.session.query(InvType).get(k)
        if inv_type is None:
            print('ERROR NONE', inv_type)
        check.ids.append(inv_type)

    # sniper ships by typeid
    check = ShipCheck(
        checkName = 'SortToSniperByShipType',
        checkTargetID = sniper_wl.id,
        checkType = check_types.SHIP_CHECK_TYPEID,
        order = 3,
        modifier = Decimal('1.00'),
        checkTag = 'sniper'
    )
    collection.checks.append(check)

    for k, v in modules.sniper_ships.items():
        inv_type = db.session.query(InvType).get(k)
        if inv_type is None:
            print('ERROR NONE', inv_type)
        check.ids.append(inv_type)

    # dps ships by market group id
    check = ShipCheck(
        checkName = 'SortToDpsByInvGroup',
        checkTargetID = dps_wl.id,
        checkType = check_types.SHIP_CHECK_INVGROUP,
        order = 4,
        modifier = Decimal('1.00'),
        checkTag = 'dps'
    )
    collection.checks.append(check)

    for k, v in modules.dps_groups.items():
        grp = db.session.query(InvGroup).get(k)
        if grp is None:
            print('ERROR NONE dps groups', k)
        check.ids.append(grp)

    # logiships by marketgroup
    check = ShipCheck(
        checkName = 'SortToLogiByInvGroup',
        checkTargetID = dps_wl.id,
        checkType = check_types.SHIP_CHECK_INVGROUP,
        order = 4,
        modifier = Decimal('1.00'),
        checkTag = 'logi'
    )
    collection.checks.append(check)

    for k, v in modules.logi_groups.items():
        grp = db.session.query(InvGroup).get(k)
        if grp is None:
            print('ERROR NONE logi invgroups', k)
        check.ids.append(grp)



if __name__ == '__main__':
    waitlistGroup = db.session.query(WaitlistGroup).filter(WaitlistGroup.groupName == 'default').one()

    logi_wl = None
    dps_wl = None
    sniper_wl = None
    for wl in waitlistGroup.waitlists:
        if wl.waitlistType == 'dps':
            dps_wl = wl
        if wl.waitlistType == 'logi':
            logi_wl = wl
        if wl.waitlistType == 'sniper':
            sniper_wl = wl

    collection = ShipCheckCollection(
        checkCollectionName = 'HQAssignments',
        waitlistGroupID = waitlistGroup.groupID,
        defaultTargetID = dps_wl.id,
        defaultTag = 'other'
    )

    db.session.add(collection)
    add_default_sorting(collection, logi_wl, dps_wl, sniper_wl)
    db.session.commit()


    waitlistGroup = db.session.query(WaitlistGroup).filter(WaitlistGroup.groupName == 'assault').one()

    logi_wl = None
    dps_wl = None
    sniper_wl = None
    for wl in waitlistGroup.waitlists:
        if wl.waitlistType == 'dps':
            dps_wl = wl
        if wl.waitlistType == 'logi':
            logi_wl = wl
        if wl.waitlistType == 'sniper':
            sniper_wl = wl

    collection = ShipCheckCollection(
        checkCollectionName = 'AssaultAssignments',
        waitlistGroupID = waitlistGroup.groupID,
        defaultTargetID = dps_wl.id,
        defaultTag = 'other'
    )

    db.session.add(collection)
    add_default_sorting(collection, logi_wl, dps_wl, sniper_wl)
    db.session.commit()


    waitlistGroup = db.session.query(WaitlistGroup).filter(WaitlistGroup.groupName == 'vanguard').one()

    logi_wl = None
    dps_wl = None
    sniper_wl = None
    for wl in waitlistGroup.waitlists:
        if wl.waitlistType == 'dps':
            dps_wl = wl
        if wl.waitlistType == 'logi':
            logi_wl = wl
        if wl.waitlistType == 'sniper':
            sniper_wl = wl

    collection = ShipCheckCollection(
        checkCollectionName = 'VanguardAssignments',
        waitlistGroupID = waitlistGroup.groupID,
        defaultTargetID = dps_wl.id,
        defaultTag = 'other'
    )

    db.session.add(collection)
    add_default_sorting(collection, logi_wl, dps_wl, sniper_wl)
    db.session.commit()

