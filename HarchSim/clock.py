class Clock:
    def __init__(self,time_step = 1e-8):
        self.clock = 0
        self.time_step = time_step

    def tick(self):
        self.clock += self.time_step