sniper_weapons = {7171: "Tachyon Modulated Energy Beam I", 3065: "Tachyon Beam Laser II",
                  2961: "1400mm Howitzer Artillery II", 9491: "1400mm 'Scout' Artillery I",
                  3090: "425mm Railgun II", 7447: "425mm Prototype Gauss Gun"
                  }
# yes I know 720mm are sniper weapons but I want the loki on dps list
dps_weapons = {2929: "800mm Repeating Cannon II", 9327: "800mm Heavy 'Scout' Repeating Cannon I",
               2420: "Torpedo Launcher II", 8117: "Prototype 'Arbalest' Torpedo Launcher",
               19739: "Cruise Missile Launcher II", 16519: "'Arbalest' Cruise Launcher I",
               3057: "Mega Pulse Laser II", 7087: "Mega Modulated Pulse Energy Beam I",
               3186: "Neutron Blaster Cannon II", 7783: "Modal Mega Neutron Particle Accelerator I",
               2969: "720mm Howitzer Artillery II"
               }

resist_ships = {17918: "Rattlesnake", 32309: "Scorpion Navy Issue", 24688: "Rokh"}
logi_ships = {11985: "Basilisk", 11978: "Scimitar", 33472: "Nestor"}

sniper_ships = {17736: "Nightmare", 17738: "Machariel", 24694: "Maelstrom",
                24688: "Rokh", 28665: "Vargur"
                }
dps_ships = {17740: "Vindicator", 24688: "Rokh", 24690: "Hyperion",
             17726: "Apocalypse Navy Issue", 32305: "Armageddon Navy Issue",
             28659: "Paladin", 28710: "Golem", 17636: "Raven Navy Issue",
             32309: "Scorpion Navy Issue", 28661: "Kronos", 32307: "Dominix Navy Issue",
             645: "Dominix", 17728: "Megathron Navy Issue", 33820: "Barghest",
             17918: "Rattlesnake", 17738: "Machariel", 17920: "Bhaalgorn",
             24694: "Maelstrom", 32311: "Typhoon Fleet Issue", 17732: "Tempest Fleet Issue",
             47271: "Leshark"
             }

dps_groups = {659: 'Supercarrier', 30: 'Titan', 547: 'Carrier'}
logi_groups = {1538: 'Force Auxiliary'}
sniper_groups = {}

t3c_ships = {29990: "Loki", 29984: "Tengu"}

none_logi_ships = {}
none_logi_ships.update(sniper_ships)
none_logi_ships.update(dps_ships)
none_logi_ships.update(resist_ships)
none_logi_ships.update(t3c_ships)

weapongroups = {'dps': {"Pulse Lasers": None, "Blasters": None, "Missile Launchers": None, "Autocannons": None, 'Entropic Disintegrators': None},
                'sniper': {"Beam Lasers": None, "Railguns": None, "Artillery Cannons": None}
                }
