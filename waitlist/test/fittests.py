import main
from waitlist import utils

if __name__ == '__main__':
    fitting = """[Vindicator, VeniVindiVG]
Damage Control II
Federation Navy Magnetic Field Stabilizer
Federation Navy Magnetic Field Stabilizer
Federation Navy Magnetic Field Stabilizer
Federation Navy Magnetic Field Stabilizer
Imperial Navy Drone Damage Amplifier
Imperial Navy Drone Damage Amplifier

Pithum C-Type Adaptive Invulnerability Field
True Sansha Stasis Webifier
Core C-Type 500MN Microwarpdrive
Pithum C-Type Adaptive Invulnerability Field
True Sansha Stasis Webifier

Neutron Blaster Cannon II
Neutron Blaster Cannon II
Neutron Blaster Cannon II
Neutron Blaster Cannon II
Neutron Blaster Cannon II
Neutron Blaster Cannon II
Neutron Blaster Cannon II
Neutron Blaster Cannon II

Large Hybrid Burst Aerator II
[Empty Rig slot]
Large Anti-EM Screen Reinforcer I


Ogre II x5

Federation Navy Antimatter Charge L x312
Null L x7128
Tracking Speed Script x1
Void L x6720
"""
print utils.parseEft(fitting)