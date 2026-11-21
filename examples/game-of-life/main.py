import random
import time

from dotenv import load_dotenv
from pixoo import Pixoo

# Load .env variables
load_dotenv()

DEAD = 0
ALIVE = 1


class Game:
    def __init__(self, size=64):
        self.size = size

        # For pixoo 64 only for now
        self.grid = [DEAD for _ in range(self.size * self.size)]

    def cell_at_xy(self, x, y):
        return self.grid[self.xy_to_index(x, y)]

    def evolve(self):
        evolved_grid = [DEAD for _ in range(self.size * self.size)]
        for row in range(self.size):
            for column in range(self.size):
                # Get the number of live cells adjacent to the cell at grid[row][col]
                number_of_alive_neighbours = self.number_of_alive_neighbours(row, column)

                # Make them DEAD
                if number_of_alive_neighbours < 2 or number_of_alive_neighbours > 3:
                    evolved_grid[self.xy_to_index(row, column)] = DEAD
                # If it was already dead, it is now ALIVE
                elif number_of_alive_neighbours == 3 and self.cell_at_xy(row, column) == DEAD:
                    evolved_grid[self.xy_to_index(row, column)] = ALIVE
                # If the number of surrounding live cells is 3 and the cell at grid[row][col] is alive keep it alive
                else:
                    evolved_grid[self.xy_to_index(row, column)] = self.cell_at_xy(row, column)

        self.grid = evolved_grid

    def load_pattern(self, pattern):
        for xy in pattern:
            self.grid[self.xy_to_index(xy[0], xy[1])] = ALIVE

    def load_random_pattern(self):
        for index in range(self.size * self.size):
            if random.randint(0, 7) == 0:
                self.grid[index] = ALIVE

    def number_of_alive_neighbours(self, row, column):
        total = 0
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x == 0 and y == 0:
                    continue

                # Wrap around the grid? For now it seems fine
                if self.cell_at_xy((row + x) % self.size, (column + y) % self.size) == ALIVE:
                    total += 1
        return total

    def xy_to_index(self, x, y):
        return y * self.size + x


def defined_value(value, default):
    return default if value is None else value


def main():
    print('[.] Booting..')

    # simulated = int(defined_value(os.environ.get('SIMULATED'), 0)) == 1
    #
    # if simulated:
    #     print('[.] Starting in simulation mode')
    # else:
    #     print('[.] Starting in connected mode')

    pixoo = Pixoo()
    pixoo.fill()
    pixoo.push()

    print('[.] Starting update loop in 2 seconds')
    time.sleep(2)

    green = (99, 199, 77)

    game = Game()
    # game.load_pattern([(2, 1), (2, 2), (2, 3)])
    game.load_random_pattern()

    def draw_game():
        pixoo.fill()
        for index, cell in enumerate(game.grid):
            if cell == ALIVE:
                pixoo.draw_pixel_at_index(index, green)
        pixoo.push()

    while True:
        try:
            # Assure a connection to the device (if the program keeps running without the screen being on
            # this will make sure it connects as soon as possible in exchange for a minor lag because of another call
            if not pixoo.validate_connection():
                time.sleep(60)
                continue

            game.evolve()
            draw_game()
            time.sleep(1)

        except KeyboardInterrupt:
            print("[.] Shutting down..")
            return


if __name__ == '__main__':
    main()
