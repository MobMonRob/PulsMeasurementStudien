class RegionOfInterest():

    def __init__(self, x, y, width, height, max_x, max_y):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_x = max_x
        self.max_y = max_y

    def move_up(self):
        if self.y > 0:
            self.y = self.y - 1

    def move_down(self):
        if self.y < self.max_y + self.height:
            self.y = self.y + 1

    def move_left(self):
        if self.x > 0:
            self.x = self.x - 1

    def move_right(self):
        if self.x < self.max_x + self.width:
            self.x = self.x + 1

    def increase_size(self):
        if self.x > 0 and self.x + self.width < self.max_x:
            if self.y > 0 and self.y + self.height < self.max_y:
                self.move_up()
                self.move_left()
                self.height = self.height + 2
                self.width = self.width + 2

    def decrease_size(self):
        if self.width > 2 and self.height > 2:
            self.move_down()
            self.move_right()
            self.height = self.height - 2
            self.width = self.width - 2

    def set_roi(self, x, y, width, height):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    def to_tuple(self):
        return (self.x, self.y, self.width, self.height)
