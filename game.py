from __future__ import annotations
import random
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Tuple, Optional, Dict, Callable, Any

# ==========================================
# ЕТАП 1 — Модель даних (ООП: інкапсуляція)
# ==========================================

class CellState(Enum):
    """Стан клітини ігрового поля"""
    EMPTY = auto()   # Порожня
    SHIP = auto()    # Корабель
    HIT = auto()     # Влучання
    MISS = auto()    # Промах

class ShotResult(Enum):
    """Результат пострілу"""
    MISS = auto()
    HIT = auto()
    SUNK = auto()

class Cell:
    """Клітина поля з інкапсульованим станом"""
    def __init__(self, state: CellState = CellState.EMPTY):
        self._state = state

    @property
    def state(self) -> CellState:
        return self._state

    @state.setter
    def state(self, value: CellState):
        self._state = value

    def __str__(self) -> str:
        symbols = {
            CellState.EMPTY: '·',
            CellState.SHIP: '■',
            CellState.HIT: 'X',
            CellState.MISS: '○'
        }
        return symbols[self._state]

class Ship:
    """Корабель з координатами, розміром та лічильником влучань"""
    def __init__(self, coordinates: List[Tuple[int, int]]):
        self.coordinates = coordinates
        self._hits = 0

    @property
    def size(self) -> int:
        return len(self.coordinates)

    def hit(self) -> bool:
        """Реєструє влучання. Повертає True, якщо корабель потоплено"""
        self._hits += 1
        return self.is_sunk()

    def is_sunk(self) -> bool:
        return self._hits >= self.size

class Board:
    """Ігрове поле з двовимірним масивом клітин та кораблями"""
    def __init__(self, size: int = 10):
        self.size = size
        self.grid: List[List[Cell]] = [[Cell() for _ in range(size)] for _ in range(size)]
        self.ships: List[Ship] = []

    def is_valid_coordinate(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def place_ship(self, coordinates: List[Tuple[int, int]]) -> bool:
        """Розміщує корабель на полі. Повертає False при невдачі"""
        for x, y in coordinates:
            if not self.is_valid_coordinate(x, y):
                return False
            if self.grid[y][x].state != CellState.EMPTY:
                return False
            # Перевірка сусідніх клітин
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if self.is_valid_coordinate(nx, ny) and self.grid[ny][nx].state == CellState.SHIP:
                        return False

        ship = Ship(coordinates)
        for x, y in coordinates:
            self.grid[y][x].state = CellState.SHIP
        self.ships.append(ship)
        return True

    def receive_shot(self, x: int, y: int) -> ShotResult:
        """Обробляє постріл по координатах та повертає результат"""
        if not self.is_valid_coordinate(x, y):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")

        cell = self.grid[y][x]
        if cell.state == CellState.HIT or cell.state == CellState.MISS:
            raise ValueError("Already shot at this cell")

        if cell.state == CellState.SHIP:
            cell.state = CellState.HIT
            # Пошук корабля, якому належить клітина
            for ship in self.ships:
                if (x, y) in ship.coordinates:
                    sunk = ship.hit()
                    return ShotResult.SUNK if sunk else ShotResult.HIT
        else:
            cell.state = CellState.MISS
            return ShotResult.MISS

        return ShotResult.MISS  # fallback

    def all_ships_sunk(self) -> bool:
        return all(ship.is_sunk() for ship in self.ships)

# ==========================================
# ЕТАП 2 — Будівництво поля (Builder)
# ==========================================

class BoardBuilder:
    """Builder для поетапного створення та заповнення поля"""
    def __init__(self):
        self._size = 10
        self._ships_to_place: List[int] = []  # розміри кораблів
        self._ships: List[List[Tuple[int, int]]] = []  # згенеровані координати

    def set_size(self, size: int) -> BoardBuilder:
        self._size = size
        return self

    def add_ship(self, size: int) -> BoardBuilder:
        self._ships_to_place.append(size)
        return self

    def validate(self) -> BoardBuilder:
        """Перевіряє можливість розміщення всіх кораблів"""
        total_cells = sum(self._ships_to_place)
        max_cells = self._size * self._size
        if total_cells > max_cells:
            raise ValueError("Too many ships for board size")
        return self

    def build(self) -> Board:
        """Створює поле та розставляє кораблі випадковим чином"""
        board = Board(self._size)
        all_coordinates: List[List[Tuple[int, int]]] = []

        for ship_size in self._ships_to_place:
            placed = False
            attempts = 1000
            while not placed and attempts > 0:
                orientation = random.choice(['H', 'V'])
                if orientation == 'H':
                    x = random.randint(0, self._size - ship_size)
                    y = random.randint(0, self._size - 1)
                    coords = [(x + i, y) for i in range(ship_size)]
                else:
                    x = random.randint(0, self._size - 1)
                    y = random.randint(0, self._size - ship_size)
                    coords = [(x, y + i) for i in range(ship_size)]

                if board.place_ship(coords):
                    placed = True
                attempts -= 1

            if not placed:
                raise RuntimeError(f"Could not place ship of size {ship_size}")

        return board

# ==========================================
# ЕТАП 3 — Створення гравців (Factory Method)
# ==========================================

class Player(ABC):
    """Абстрактний гравець"""
    def __init__(self, name: str, board: Board):
        self.name = name
        self.board = board

    @abstractmethod
    def make_shot(self, opponent_board: Board) -> Tuple[int, int]:
        pass

class HumanPlayer(Player):
    """Гравець-людина: зчитує координати з консолі"""
    def make_shot(self, opponent_board: Board) -> Tuple[int, int]:
        while True:
            try:
                coords = input(f"{self.name}, введіть координати (x y): ").strip().split()
                if len(coords) != 2:
                    print("Помилка: введіть два числа через пробіл")
                    continue
                x, y = map(int, coords)
                if not opponent_board.is_valid_coordinate(x, y):
                    print("Координати поза межами поля")
                    continue
                if opponent_board.grid[y][x].state in (CellState.HIT, CellState.MISS):
                    print("Сюди вже стріляли")
                    continue
                return x, y
            except ValueError:
                print("Помилка: введіть цілі числа")

class BotPlayer(Player):
    """Бот, що делегує вибір координат стратегії"""
    def __init__(self, name: str, board: Board, strategy):
        super().__init__(name, board)
        self.strategy = strategy

    def make_shot(self, opponent_board: Board) -> Tuple[int, int]:
        return self.strategy.choose(opponent_board)

class PlayerFactory:
    """Фабрика гравців (Factory Method)"""
    @staticmethod
    def create(player_type: str, name: str, board: Board, **kwargs) -> Player:
        if player_type == "human":
            return HumanPlayer(name, board)
        elif player_type == "bot":
            strategy = kwargs.get("strategy", RandomStrategy())
            return BotPlayer(name, board, strategy)
        else:
            raise ValueError(f"Unknown player type: {player_type}")

# ==========================================
# ЕТАП 4 — ШІ бота (Strategy)
# ==========================================

class ShotStrategy(ABC):
    """Інтерфейс стратегії вибору пострілу"""
    @abstractmethod
    def choose(self, board: Board) -> Tuple[int, int]:
        pass

class RandomStrategy(ShotStrategy):
    """Випадкова вільна клітина"""
    def choose(self, board: Board) -> Tuple[int, int]:
        available = []
        for y in range(board.size):
            for x in range(board.size):
                if board.grid[y][x].state not in (CellState.HIT, CellState.MISS):
                    available.append((x, y))
        return random.choice(available) if available else (0, 0)

class SmartStrategy(ShotStrategy):
    """Після влучання добиває корабель по сусідніх клітинах"""
    def __init__(self):
        self._hits_stack: List[Tuple[int, int]] = []
        self._target_mode = False
        self._initial_hit: Optional[Tuple[int, int]] = None
        self._directions_tried: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        self._current_direction: Optional[Tuple[int, int]] = None

    def choose(self, board: Board) -> Tuple[int, int]:
        # Збираємо всі доступні клітини (для випадкового вибору як фолбек)
        available = []
        for y in range(board.size):
            for x in range(board.size):
                state = board.grid[y][x].state
                if state not in (CellState.HIT, CellState.MISS):
                    available.append((x, y))

        # Якщо є активна ціль, намагаємось добити
        if self._target_mode and self._current_direction:
            last_hit = self._hits_stack[-1]
            next_x = last_hit[0] + self._current_direction[0]
            next_y = last_hit[1] + self._current_direction[1]

            if board.is_valid_coordinate(next_x, next_y) and (next_x, next_y) in available:
                return next_x, next_y
            else:
                # Змінюємо напрямок на протилежний від початкового влучання
                if self._initial_hit:
                    self._current_direction = (-self._current_direction[0], -self._current_direction[1])
                    # Перевіряємо протилежний напрямок
                    for _ in range(len(board.ships)):  # максимальна довжина корабля
                        next_x = self._initial_hit[0] + self._current_direction[0]
                        next_y = self._initial_hit[1] + self._current_direction[1]
                        if board.is_valid_coordinate(next_x, next_y) and (next_x, next_y) in available:
                            return next_x, next_y
                        # Не знайшли, скидаємо режим
                self._target_mode = False
                self._current_direction = None
                self._initial_hit = None
                self._hits_stack.clear()

        return random.choice(available)

    def notify_result(self, x: int, y: int, result: ShotResult):
        """Оновлює стан стратегії на основі результату пострілу"""
        if result == ShotResult.HIT:
            if not self._target_mode:
                self._target_mode = True
                self._initial_hit = (x, y)
                self._hits_stack = [(x, y)]
                # Спробуємо перший випадковий напрямок
                directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
                self._current_direction = random.choice(directions)
            else:
                self._hits_stack.append((x, y))
        elif result == ShotResult.SUNK:
            self._target_mode = False
            self._current_direction = None
            self._initial_hit = None
            self._hits_stack.clear()

# ==========================================
# ЕТАП 5 — Постріл як об'єкт (Command)
# ==========================================

class ShotCommand:
    """Команда пострілу з можливістю скасування (undo)"""
    def __init__(self, board: Board, x: int, y: int):
        self.board = board
        self.x = x
        self.y = y
        self._previous_state: Optional[CellState] = None
        self._executed = False

    def execute(self) -> ShotResult:
        if self._executed:
            raise RuntimeError("Command already executed")
        self._previous_state = self.board.grid[self.y][self.x].state
        result = self.board.receive_shot(self.x, self.y)
        self._executed = True
        return result

    def undo(self):
        if not self._executed:
            return
        if self._previous_state is not None:
            # Складне скасування для кораблів (спрощено для демонстрації)
            self.board.grid[self.y][self.x].state = self._previous_state
            self._executed = False

# ==========================================
# ЕТАП 6 — Події (Observer)
# ==========================================

class EventBus:
    """Шина подій: компоненти підписуються та отримують сповіщення"""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, handler: Callable):
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(handler)

    def emit(self, event: str, data: Any = None):
        if event in self._subscribers:
            for handler in self._subscribers[event]:
                handler(data)

# ==========================================
# ЕТАП 8 — Відображення (Single Responsibility)
# ==========================================

class ConsoleRenderer:
    """Відповідає за відображення ігрового поля в консолі"""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe('on_hit', lambda d: self._on_event('on_hit', d))
        self.event_bus.subscribe('on_miss', lambda d: self._on_event('on_miss', d))
        self.event_bus.subscribe('on_ship_sunk', lambda d: self._on_event('on_ship_sunk', d))
        self.event_bus.subscribe('on_game_over', lambda d: self._on_event('on_game_over', d))

    def _on_event(self, event: str, data: Any):
        if event == 'on_hit':
            print(f"💥 Влучання по координатах {data}!")
        elif event == 'on_miss':
            print(f"🌊 Промах по координатах {data}!")
        elif event == 'on_ship_sunk':
            print(f"🚢 Корабель потоплено!")
        elif event == 'on_game_over':
            print(f"🏆 Гра завершена! Переможець: {data}")

    def render(self, player_board: Board, opponent_board: Board, player_name: str):
        """Малює обидва поля: своє та противника"""
        print(f"\n{'='*50}")
        print(f"Хід гравця: {player_name}")
        print(f"{'='*50}")
        print("Ваше поле:")
        self._print_board(player_board, hide_ships=False)
        print("\nПоле противника:")
        self._print_board(opponent_board, hide_ships=True)

    def _print_board(self, board: Board, hide_ships: bool = False):
        # Верхня шкала
        print("   " + " ".join(str(i) for i in range(board.size)))
        print("  " + "──" * board.size)
        for y in range(board.size):
            row = f"{y} │"
            for x in range(board.size):
                cell = board.grid[y][x]
                if hide_ships and cell.state == CellState.SHIP:
                    row += f"{str(Cell(CellState.EMPTY))} "
                else:
                    row += f"{str(cell)} "
            print(row)

# ==========================================
# ЕТАП 7 — Стани гри (State)
# ==========================================

class GameState(ABC):
    """Абстрактний стан гри"""
    @abstractmethod
    def handle(self, game: Game):
        pass

class SetupState(GameState):
    """Стан розстановки кораблів"""
    def handle(self, game: Game):
        print("\n=== Розстановка кораблів ===")
        # Створюємо поля через Builder
        builder = BoardBuilder().set_size(10)
        for size in [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]:  # стандартний набір
            builder.add_ship(size)
        builder.validate()

        game.player1.board = builder.build()
        game.player2.board = builder.build()

        game.state = PlayState()
        game.state.handle(game)

class PlayState(GameState):
    """Стан ігрового процесу"""
    def handle(self, game: Game):
        current_player = game.player1
        opponent = game.player2

        while True:
            game.renderer.render(current_player.board, opponent.board, current_player.name)

            x, y = current_player.make_shot(opponent.board)

            # ЕТАП 5: Використовуємо Command
            command = ShotCommand(opponent.board, x, y)
            result = command.execute()
            game.shot_history.append(command)

            # ЕТАП 6: Генеруємо події
            if result == ShotResult.MISS:
                game.event_bus.emit('on_miss', (x, y))
            elif result == ShotResult.HIT:
                game.event_bus.emit('on_hit', (x, y))
            elif result == ShotResult.SUNK:
                game.event_bus.emit('on_ship_sunk', (x, y))

            # Оновлюємо стратегію бота (якщо це бот)
            if isinstance(current_player, BotPlayer):
                current_player.strategy.notify_result(x, y, result)

            # Перевірка завершення
            if opponent.board.all_ships_sunk():
                game.winner = current_player
                game.state = GameOverState()
                game.state.handle(game)
                return

            # Зміна ходу
            if result == ShotResult.MISS:
                current_player, opponent = opponent, current_player

class GameOverState(GameState):
    """Стан завершення гри"""
    def handle(self, game: Game):
        game.event_bus.emit('on_game_over', game.winner.name)
        print(f"\nПереможець: {game.winner.name}!")

# ==========================================
# Головний клас Game (координатор)
# ==========================================

class Game:
    """Центральний клас гри, що об'єднує всі компоненти"""
    def __init__(self):
        self.event_bus = EventBus()
        self.renderer = ConsoleRenderer(self.event_bus)
        self.shot_history: List[ShotCommand] = []

        # Створюємо гравців через фабрику (ЕТАП 3)
        self.player1 = PlayerFactory.create("human", "Гравець", Board())
        self.player2 = PlayerFactory.create(
            "bot", "Комп'ютер", Board(),
            strategy=SmartStrategy()  # ЕТАП 4: вибір стратегії
        )

        self.winner: Optional[Player] = None
        self.state: GameState = SetupState()

    def start(self):
        """Запускає гру"""
        print("=== МОРСЬКИЙ БІЙ ===")
        self.state.handle(self)

# ==========================================
# Точка входу
# ==========================================

if __name__ == "__main__":
    game = Game()
    game.start()