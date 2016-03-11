class FleetStatus:
    """
    self.status = Text with status
    self.fc = [name, id]
    self.manager = [name, id]
    self.constellation = [name, id]
    self.dock = [name, id]
    self.systemhq = [name, id]
    self.systemsas = [[name, id], ...]
    self.systemsvg = [[name, id], ...]
    """
    def __init__(self):
        self.status = "Down"
        self.fc = None
        self.manager = None
        self.constellation = None
        self.dock  = None
        self.systemhq = None
        self.systemsas = None
        self.systemsvg = None

fleet_status = FleetStatus()