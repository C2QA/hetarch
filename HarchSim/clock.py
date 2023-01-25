class Clock:
    def __init__(self,clock_speed = 1e-8):
        self.clock = 0
        self.clock_speed = clock_speed

    def tick(self):
        self.clock += self.clock_speed