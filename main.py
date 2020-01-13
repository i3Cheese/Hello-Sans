import os
import sys
from math import ceil, sqrt, pi, cos, sin
import random
from typing import Tuple, Set, List, Union, Optional, Dict, NoReturn
from pygame.rect import RectType

# инициализация pygame
import pygame as pg

FPS = 30
pg.init()
SIZE = WIDTH, HEIGHT = 600, 600
screen = pg.display.set_mode(SIZE)
clock = pg.time.Clock()
running = True

MINIMUM_LIGHT = 4
UPDATE_FRAME = 10

Point = Tuple[float, float]
IntPoint = Tuple[int, int]
UserData = Dict[str, str]
LightSource = Tuple[IntPoint, int]
Color = Union[Tuple[int, int, int], Tuple[int, int, int, int], pg.Color]

FONT = pg.font.Font(None, 35)

SAVE_FILE = 'stealth_light.save'
ENCODING = 'utf-8'

VOLUME = .5


def load_music(name: str):
    fullname = os.path.join('data', name)
    return pg.mixer.Sound(fullname)


# IMAGE TOOLS


def load_image(name: str,
               colorkey: Optional[Union[int, Tuple[int, int, int]]] = None) -> pg.Surface:
    fullname = os.path.join('data', name)
    image = pg.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        if colorkey == -2:
            colorkey = (0, 0, 0)
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def cut_sheet(sheet: pg.Surface, columns: int, rows: int) -> Tuple[pg.Rect, List[pg.Surface]]:
    rect = pg.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
    frames = []
    for j in range(rows):
        for i in range(columns):
            frame_location = (rect.w * i, rect.h * j)
            # self.rect.size - это кортеж (w, h)
            frames.append(sheet.subsurface(pg.Rect(frame_location, rect.size)))
    return rect, frames


def find_center(s: pg.sprite.Sprite) -> IntPoint:
    return s.rect.center


# WINDOW TOOLS


def terminate() -> NoReturn:
    pg.quit()
    sys.exit()


def some_screen(text: Optional[List[str]],
                image: str,
                color: Color = (0, 0, 0),
                track: str = 'menu') -> None:
    """Печатает text цвета color на фоне image и выводит на экран до нажатия на любую кнопку."""
    surf = pg.Surface(SIZE)

    fon = pg.transform.scale(load_image(image), (WIDTH, HEIGHT))
    surf.blit(fon, (0, 0))
    if text:
        text_coord = 200
        for line in text:
            string_rendered = FONT.render(line, 1, color)
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = 10
            text_coord += intro_rect.height
            surf.blit(string_rendered, intro_rect)

    finished = False

    music.play(track)

    # Что бы не закрыть экран сразу после открытия
    pg.display.flip()
    pg.time.wait(600)
    pg.event.clear()
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                terminate()
            elif event.type == pg.MOUSEBUTTONUP or event.type == pg.KEYUP:
                finished = True

        if finished:
            break

        screen.blit(surf, (0, 0))
        mouse.update()
        mouse.draw(screen)

        pg.display.flip()
        clock.tick(FPS)


def death_screen() -> None:
    """Выводит на экран информацию о смерти."""

    text = ["Вы умерли!",
            "В следующий раз будьте аккуратны",
            "",
            "",
            "Нажмите любую клавишу что бы продолжить"]

    some_screen(text, 'death_fon.png', (0, 0, 0), 'dead')


def win_screen(level_num: Union[int, str]) -> None:
    """Выводит на экран информацию о прохождении уровня или игры или произвольный текст."""

    if isinstance(level_num, int):
        text = [f"Вы прошли уровень {level_num}!",
                "В следующий раз будьте аккуратны.",
                "",
                "Нажмите любую клавишу что бы продолжить."]
        color = (210, 255, 255)
        img = 'win_fon.png'
    elif level_num == 'all game':
        text = ["Вы прошли всю игру!",
                "Поздравлям!",
                "Спасибо, что были с нами.",
                "",
                "Нажмите любую клавишу что бы продолжить."]
        color = (0, 0, 0)
        img = 'all_game_win_fon.png'
    else:
        text = level_num.split('\n')
        color = (255, 255, 255)
        img = 'win_fon.png'

    some_screen(text, img, color, 'menu')


def hello_screen() -> None:
    some_screen(None, 'hello_fon.png')


def control_screen() -> None:
    some_screen(None, 'control.png')


# OTHER TOOLS


def sign(a: float) -> int:
    """Возвращает знак числа"""
    return -1 if a < 0 else 1


def read_saved_data() -> UserData:
    """Читает сохранёную информацию."""

    dictionary = dict()
    if os.path.isfile(SAVE_FILE):
        with open(SAVE_FILE, 'r', encoding=ENCODING) as f:
            line = f.readline()
            while line:
                a, b = line.strip().split('=')
                dictionary[a] = b
                line = f.readline()

    return dictionary


def save_data(dictionary: UserData) -> None:
    """Сохранение данных."""
    with open(SAVE_FILE, 'w', encoding=ENCODING) as f:
        for key, data in dictionary.items():
            f.write(f'{key}={data}')


# CLASSES


class MusicPlayer:
    music_channel: pg.mixer.Channel
    sound_channels: List[pg.mixer.Channel]
    musics = {'menu': load_music('mus_menu.oga'),
              'pause': load_music('mus_pause.oga'),
              'game': load_music('mus_battle.oga'),
              'dead': load_music('mus_dead.ogg')}

    music_volume = .5
    sound_volume = .7

    def __init__(self):

        self.now_play = ''
        pg.mixer.set_num_channels(6)
        self.music_channel = pg.mixer.Channel(0)
        self.music_channel.set_volume(self.music_volume)

        self.sound_channels = []
        self.last_channel = 0
        for i in range(1, 6):
            self.sound_channels.append(pg.mixer.Channel(i))
            self.sound_channels[-1].set_volume(self.sound_volume)

    def play(self, name: str) -> None:
        if name == self.now_play:
            return

        self.now_play = name
        self.music_channel.play(self.musics[self.now_play], -1)

    def pause(self):
        pg.mixer.music.pause()

    def make_sound(self, sound: pg.mixer.Sound, l_vol: float = 1, r_vol: float = 1):
        self.last_channel += 1
        self.last_channel %= len(self.sound_channels)
        self.sound_channels[self.last_channel].set_volume(l_vol * self.sound_volume,
                                                          r_vol * self.sound_volume)
        self.sound_channels[self.last_channel].play(sound, 0)


class Button(pg.sprite.Sprite):
    """Создан для различных меню. Выполняет переданную функцию при нажатии."""
    img = load_image('button.png')
    default_rect = img.get_rect()

    def __init__(self, text: str, func, *groups,
                 pos: Optional[IntPoint] = None,
                 center_pos: Optional[IntPoint] = None):
        super().__init__(*groups)

        self.func = func

        self.image = self.img.copy()
        self.rect = self.image.get_rect()
        if pos:
            self.rect.topleft = pos
        else:
            self.rect.center = center_pos

        string_rendered = FONT.render(text, 1, pg.Color('black'))
        text_rect = string_rendered.get_rect()
        text_rect.center = self.rect.w // 2, self.rect.h // 2
        self.image.blit(string_rendered, text_rect)

    def update(self, *args):
        if args and isinstance(args[0], pg.event.EventType):
            event = args[0]
            # вызываем функцию при нажатии
            if event.type == pg.MOUSEBUTTONUP and event.button == pg.BUTTON_LEFT:
                if self.rect.collidepoint(pg.mouse.get_pos()):
                    self.func()


class Menu(pg.Surface):
    """Произвольное меню с кнопками. Полностью перехватывает управление."""

    def __init__(self):
        super().__init__(SIZE)
        self.buttons_group = pg.sprite.Group()
        self.finished = False  # Если истина - завершаем внутриний цикл.

    def run(self):
        """Обрабатываем поступающие евенты."""
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    terminate()
                elif event.type == pg.MOUSEBUTTONUP:
                    self.buttons_group.update(event)

            if self.finished:
                break

            screen.blit(self, (0, 0))
            mouse.update()
            mouse.draw(screen)

            pg.display.flip()
            clock.tick(FPS)


class MainMenu(Menu):
    """Меню начала игры. Изменяет level"""

    def __init__(self):
        super().__init__()

        self.blit(pg.transform.scale(load_image("menu_fon.png"), SIZE), (0, 0))

        # создаём кнопки
        Button('Новая игра', self.start_new_game, self.buttons_group,
               pos=(0, HEIGHT - Button.default_rect.height))
        Button('Продолжить', self.continue_a_game, self.buttons_group,
               pos=(WIDTH // 2, HEIGHT - Button.default_rect.height))

        self.buttons_group.draw(self)

        self.finished = False  # Если тру - завершаем внутриний цикл.

        music.play('menu')  # Запускаем музыку
        self.run()

    def continue_a_game(self):
        global level
        dictionary = read_saved_data()
        if 'level' not in dictionary:
            pass
        else:
            level = Level(int(dictionary['level']))
            self.finished = True

    def start_new_game(self):
        global level
        level = Level(1)
        self.finished = True


class Pause(Menu):
    """Окно игровой паузы"""

    def __init__(self):
        super().__init__()

        self.blit(pg.transform.scale(load_image("pause_fon.png"), SIZE), (0, 0))

        # Создаём кнопки
        Button('Меню', self.open_menu, self.buttons_group, pos=(0, 0))
        Button('Продолжить', self.back_to_game, self.buttons_group, pos=(WIDTH // 2, 0))
        self.buttons_group.draw(self)

        music.play('pause')  # Запускаем музыку
        self.run()

    def open_menu(self):
        self.finished = True
        MainMenu()

    def back_to_game(self):
        self.finished = True


class LightedSprite(pg.sprite.Sprite):
    """Класс для поддержки освёщености спрайтов."""
    frame_from_last_light_update: int
    monochrome: bool  # Определяет как будет накладываться затемнение
    real_image: Optional[pg.Surface]  # Картинка без затемнения
    _image: Optional[pg.Surface]
    _light: int

    def __init__(self, *groups, level, monochrome=True):
        super().__init__(*groups, level.light_sprites)
        self.frame_from_last_light_update = random.randrange(0, UPDATE_FRAME)
        self.level = level

        self.monochrome = monochrome
        self.real_image = None
        self._image = None
        self._light = MINIMUM_LIGHT

    @property
    def image(self) -> pg.Surface:
        return self._image

    @image.setter
    def image(self, value: pg.Surface):
        self.real_image = value
        self.put_light()

    @property
    def light(self) -> int:
        return self._light

    @light.setter
    def light(self, value):
        if self._light == value:
            return
        self._light = value
        self.put_light()

    def put_light(self) -> None:
        self._image = self.real_image.copy()
        dark_image = self._image.copy()
        r = dark_image.get_rect()
        dark = 255 - max(0, min(255, self.light))
        if self.monochrome:
            dark_image.fill((0, 0, 0, dark))
        else:
            # Сохраняем отношения прозрачности. В частности прозрачное остаётся прозрачным
            for i in range(r.h):
                for j in range(r.w):
                    dark_image.set_at((j, i), (0, 0, 0, dark_image.get_at((j, i)).a * dark // 255))
        self._image.blit(dark_image, (0, 0))

    @property
    def tracking_points(self) -> List[IntPoint]:
        return [self.rect.topleft,
                self.rect.topright,
                self.rect.bottomleft,
                self.rect.bottomright]

    def update(self, *args) -> None:
        if isinstance(self, MoveableSprite):
            self.frame_from_last_light_update += 1
            if self.frame_from_last_light_update >= UPDATE_FRAME:
                self.frame_from_last_light_update = 0
                self.level.relight_it(self)


class AnimationSprite:
    """Класс для обеспечения анимации спрайтов."""

    def __init__(self, update_image_speed):
        self.update_image_speed = update_image_speed
        self._stay = True if isinstance(self, MoveableSprite) else False
        self.cur_frame = random.randrange(0, update_image_speed * len(self.frames))
        self.image = self.frames[self.cur_frame // self.update_image_speed]
        self.mask = pg.mask.from_surface(self.image)

    def update(self) -> None:
        """Обновляет текущий кадр"""
        if not self.stay:
            self.cur_frame = (self.cur_frame + 1) % (len(self.frames) * self.update_image_speed)
            self.image = self.frames[self.cur_frame // self.update_image_speed]
            self.mask = pg.mask.from_surface(self.image)

    @property
    def stay(self) -> bool:
        return self._stay

    @stay.setter
    def stay(self, check: bool):
        if check:
            self.cur_frame = 0
            self.image = self.frames[0]

        self._stay = check


class MoveableSprite:
    """Класс для обеспечения передвежения спрайтов с некоторой скоростью."""
    real_pos: List[float]
    speed: float

    def __init__(self, pos: Point, speed: float):
        self.speed = speed
        self.real_pos = list(pos)

    def move(self, dx: float, dy: float) -> None:
        """Передвигает спрайт на расстояние self.speed по лучу
            задаваемым вектором с координатами {dx, dy}"""
        if not dx and not dy:
            return None
        elif not dy:
            dx, dy = self.speed * sign(dx), 0
        elif not dx:
            dx, dy = 0, self.speed * sign(dy)
        else:
            r = sqrt(dx ** 2 + dy ** 2)
            dx, dy = self.speed * dx / r, self.speed * dy / r

        self.change_cords_and_push_from_walls(dx, dy)

    def change_cords_and_push_from_walls(self, dx: float, dy: float) -> None:
        """Изменяем координаты и выталкиваем персонажа из стен"""
        if dx:
            self.real_pos[0] += dx
            self.rect.x = round(self.real_pos[0])
            sign_x = sign(dx)
            while pg.sprite.spritecollideany(self, self.level.collided_sprites):
                self.real_pos[0] -= sign_x
                self.rect.x -= sign_x
        if dy:
            self.real_pos[1] += dy
            self.rect.y = round(self.real_pos[1])
            sign_y = sign(dy)
            while pg.sprite.spritecollideany(self, self.level.collided_sprites):
                self.real_pos[1] -= sign_y
                self.rect.y -= sign_y  # выталкивает персонажа из стен

    def move_to(self, pos: Point) -> bool:
        """Передвегаем спрайк к точке, с заданой скоростью.
        Возращает истунну если растояние до точки меньше скорости.
        (Спрайт дойдёт до точки если ему не помешают стены)"""

        dx, dy = pos[0] - self.rect.x, pos[1] - self.rect.y
        r = sqrt(dx ** 2 + dy ** 2)
        if r == 0:
            return True
        if r <= self.speed:
            self.change_cords_and_push_from_walls(dx, dy)
            return True
        else:
            self.move(dx, dy)
            return False


class Tile(LightedSprite):
    tile_images = {'wall': load_image('wall.png'), 'empty': load_image('empty.png')}

    def __init__(self, image_type: str, is_collide: bool, pos_x: int, pos_y: int, level):
        # Инициализируем спрайт и освещение
        super().__init__(level.tiles_group, level.all_sprites,
                         monochrome=True,
                         level=level)
        if is_collide:
            self.add(level.collided_sprites)
        self.is_collide = is_collide
        self.image = Tile.tile_images[image_type]
        self.rect = pg.Rect(level.tile_width * pos_x, level.tile_height * pos_y,
                            level.tile_width, level.tile_height, )


class Participle(LightedSprite):
    # Создаём различные изобржания частиц
    fire = []
    for scale in [1, 2, 3]:
        for color in [(255, 0, 0), (253, 240, 69), (0, 0, 0)]:
            __img = pg.Surface((scale, scale), pg.SRCALPHA)
            __img.fill(color)
            fire.append(__img)

    def __init__(self, pos, level, light, live_frames=30):
        super().__init__(level.all_sprites,
                         level.participles_group,
                         level=level,
                         monochrome=True)

        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()
        self.light = light

        # у каждой частицы своя скорость — это вектор
        self.velocity = [random.random() - 1 / 2, random.random() - 1 / 2]
        # и свои координаты
        self.rect.topleft = pos
        self.real_pos = list(pos)

        self.live_frames = live_frames  # Сколько кадров будет существовать частица

    def update(self, *args):
        if args:
            return

        # перемещаем частицу
        self.real_pos[0] += self.velocity[0]
        self.real_pos[1] += self.velocity[1]
        self.rect.x = round(self.real_pos[0])
        self.rect.y = round(self.real_pos[1])

        # убиваем частицу, если она прожила своё время
        self.live_frames -= 1
        if self.live_frames <= 0:
            self.kill()


class Torch(LightedSprite, AnimationSprite):
    default_rect, frames = cut_sheet(load_image("torch_sheet.png"), 4, 1)

    def __init__(self, pos_of_center: IntPoint, level):
        super().__init__(level.all_sprites, level.objects_group, level.useable_objects_group,
                         monochrome=False,
                         level=level)

        AnimationSprite.__init__(self, update_image_speed=10)

        self.rect = self.default_rect.copy()
        self.rect.center = pos_of_center

        self.frame_from_last_participle_create = random.randrange(0, UPDATE_FRAME)

        self.light_power = 255
        self.level.add_light((self.rect.center, self.light_power))
        self.level.relight_it(self)

    def use(self, player):
        if player.add_torch():  # Если игрок смог взять факел - убираем его из игры.
            self.level.remove_light((self.rect.center, self.light_power))
            self.kill()

    def update(self, *args):
        # изменяем кадр
        if args:  # Пропускаем евенты нажатия на клавиш и т.п.
            pass
        else:
            # Находится ли спрайт в зоне видимоти
            if not self.rect.colliderect(self.level.visible_area):
                return

            AnimationSprite.update(self)  # Обновляем анимацию

            # Создаём частицы, искры и пепел.
            self.frame_from_last_participle_create += 1
            if self.frame_from_last_participle_create >= UPDATE_FRAME:
                self.frame_from_last_participle_create = 0
                for i in range(2):
                    Participle((self.rect.centerx, self.rect.centery - 10), self.level, self.light)
        super().update(*args)


class Exit(LightedSprite):
    """Выход с уровня."""
    default_image = load_image('exit.png')

    def __init__(self, pos_x: int, pos_y: int, level):
        # Инициализируем спрайт и освещение
        super().__init__(level.all_sprites, level.objects_group, level.useable_objects_group,
                         monochrome=False,
                         level=level)
        # Задаём координаты
        self.image = self.default_image
        self.rect = self.image.get_rect().move(level.tile_width * pos_x, level.tile_height * pos_y)

    def use(self, player):
        player.win()


class Border(pg.sprite.Sprite):
    """Невидимая преграда."""

    def __init__(self, rect: pg.Rect, level):
        super().__init__(level.all_sprites, level.collided_sprites)
        self.image = pg.Surface(rect.size, pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Делаем невидимым
        self.rect = rect
        self.mask = pg.Mask(rect.size, True)


class Player(LightedSprite, AnimationSprite, MoveableSprite):
    inventory: Dict[str, List[int]]
    inventory_icon_size = (20, 20)
    inventory_icons: Dict[str, pg.Surface] = {
        'torch': pg.transform.scale(load_image('torch.png'), inventory_icon_size)}

    default_rect, frames = cut_sheet(load_image('player_sheet.png'), 4, 1)

    def __init__(self, pos_x, pos_y, level):
        # Инициализируем спрайт и освещение
        super().__init__(level.all_sprites, level.player_group,
                         level=level,
                         monochrome=False)
        self.rect = Player.default_rect.copy()
        self.rect.bottom = (pos_y + 1) * self.level.tile_height
        self.rect.centerx = int((pos_x + .5) * self.level.tile_width)

        AnimationSprite.__init__(self,  # иницаилизируем анимацию
                                 update_image_speed=10)
        MoveableSprite.__init__(self,  # инициализируем двжение
                                pos=self.rect.topleft,
                                speed=5)

        # Значения - текущее кол-во и вместимость
        self.inventory = {"torch": [3, 3]}

        self.level.relight_it(self)

    def update(self, *args):
        if args:
            if isinstance(args[0], pg.event.EventType):
                event = args[0]
                if event.type == pg.KEYUP and event.key == pg.K_e:
                    # пытаемся использовать что-либо или поставить факел.
                    use_that = pg.sprite.spritecollideany(self, level.useable_objects_group)
                    if use_that is None:
                        self.place_torch()
                    else:
                        use_that.use(self)

        else:
            # Определяем направление движения
            dx = 0
            dy = 0
            if pg.key.get_pressed()[pg.K_w]:
                dy -= self.speed
            if pg.key.get_pressed()[pg.K_s]:
                dy += self.speed
            if pg.key.get_pressed()[pg.K_a]:
                dx -= self.speed
            if pg.key.get_pressed()[pg.K_d]:
                dx += self.speed

            self.stay = not (dx or dy)
            MoveableSprite.move(self, dx, dy)

            # изменяем кадр
            AnimationSprite.update(self)

        super().update(*args)

    def add_torch(self) -> bool:
        """Добавляет факел в инвентарь если есть место."""
        torchs = self.inventory["torch"]
        if torchs[0] < torchs[1]:
            torchs[0] += 1
            return True
        else:
            return False

    def place_torch(self) -> None:
        """Ставит факел на карту из инвентаря"""
        if self.inventory["torch"][0]:
            Torch(find_center(self), self.level)
            self.inventory["torch"][0] -= 1

    def death(self):
        """Игрок умирает"""
        death_screen()
        MainMenu()

    def win(self):
        """Игрок прошёл уровень"""
        self.level.win()

    def draw_inventory(self) -> pg.Surface:
        """Возвращает прозрачный прямоугольник с информацией о содержании инвентаря."""
        one_line_height = self.inventory_icon_size[1] + 5
        surf = pg.Surface((80, len(self.inventory) * one_line_height),
                          pg.SRCALPHA, self.level)
        surf.set_alpha(0)

        for i, (key, value) in enumerate(self.inventory.items()):
            surf.blit(self.inventory_icons[key], (0, i * one_line_height))
            line = f'{value[0]} / {value[1]}'
            line_rendered = FONT.render(line, True, (180, 180, 180))
            surf.blit(line_rendered, (self.inventory_icon_size[0], i * one_line_height))

        return surf


class Enemy(LightedSprite, AnimationSprite, MoveableSprite):
    default_rect, frames = cut_sheet(load_image('enemy_sheet.png'), 4, 1)
    player_priority = 100000

    def __init__(self, pos_x: int, pos_y: int, level):
        # Инициализируем спрайт и освещение
        super().__init__(level.all_sprites, level.enemies_group,
                         monochrome=False,
                         level=level)
        # Задаём координаты
        self.rect = self.default_rect.copy().move(level.tile_width * pos_x,
                                                  level.tile_height * pos_y)

        AnimationSprite.__init__(self,  # иницаилизируем анимацию
                                 update_image_speed=10)
        MoveableSprite.__init__(self,  # инициализируем двжение
                                pos=self.rect.topleft,
                                speed=3)

        # инициализация зрения
        self.visual_range = 256
        self.num_of_rays = 40
        self.target: Optional[Point] = None
        self.frame_from_last_look = 0

        # Инициализация звуков.
        self.audibility_radius = 256
        self.sound_update_frame = random.randint(3 * FPS, 7 * FPS)
        self.frame_from_last_cry = random.randint(0, self.sound_update_frame)
        self.cry_sound = load_music(random.choice(['cry.ogg', 'cry1.ogg']))

        self.level.relight_it(self)

    def update(self, *args) -> None:
        if args:
            pass
        else:
            # Находится ли спрайт в зоне видимоти
            if not self.rect.colliderect(self.level.visible_area):
                return

            # Зрение
            self.frame_from_last_look += 1
            if self.frame_from_last_look >= UPDATE_FRAME:
                self.frame_from_last_look = 0
                self.target = self.look_around()

            # Движение
            if self.target:
                if MoveableSprite.move_to(self, self.target):
                    self.target = None
                    self.stay = True
                else:
                    self.stay = False

            # Звуки
            self.frame_from_last_cry += 1
            if self.frame_from_last_cry >= self.sound_update_frame:
                self.frame_from_last_cry = 0
                self.make_sound()

            if pg.sprite.collide_mask(self, self.level.player):
                self.level.player.death()

            # изменяем кадр
            AnimationSprite.update(self)

        super().update(*args)

    def look_around(self) -> Optional[Point]:
        """Запускает несколько лучей вокруг себя. Возвращает наиболее приоритетную цель"""
        now_angle = 0
        delta_angle = 2 * pi / self.num_of_rays
        target: Optional[Point] = None
        priority_of_target = 0
        for _ in range(self.num_of_rays):
            new_target, new_priority_of_target = self.look_to(
                self.visual_range * cos(now_angle),
                self.visual_range * sin(now_angle),
                self.visual_range)
            if new_priority_of_target >= priority_of_target:
                target = new_target
                priority_of_target = new_priority_of_target
            now_angle += delta_angle

        if target is None:
            return None
        else:
            return target[0] - self.rect.width // 2, target[1] - self.rect.height // 2
        # Для стремления прийти в эту точку центром.

    def look_to(self, dx: float, dy: float, r: Optional[float] = None) \
            -> Tuple[Optional[Point], int]:
        """Запускает луч до pos, возвращаем максимальное приоритетную точку и её приоритет.
        Приоритет тем выше тем выше освещеность точки. У игрока максимальный приоритет. """
        target = None
        target_priority = 0

        if r is None:
            r = sqrt(dx ** 2 + dy ** 2)
        if r <= 0:
            return target, target_priority

        m = 20  # Модификатор. Ускоряет просчёт

        r /= m
        r = ceil(r)
        dx = dx / r
        dy = dy / r
        new_cord = list(self.rect.center)
        for _ in range(int(r) + 1):
            tile = self.level.cords_to_tile(new_cord)
            if tile is not None:
                if tile.light > MINIMUM_LIGHT:
                    if self.level.player.rect.collidepoint(*new_cord):
                        target = self.level.player.rect.center
                        target_priority = self.player_priority
                    if tile.light >= target_priority:
                        target = tuple(new_cord)
                        target_priority = tile.light
                if tile.is_collide:
                    break
            new_cord[0] += dx
            new_cord[1] += dy
        return target, target_priority

    def make_sound(self):
        dx = self.level.player.rect.centerx - self.rect.centerx
        dy = self.level.player.rect.centery - self.rect.centery
        r = sqrt(dx ** 2 + dy ** 2)
        if r >= self.audibility_radius:
            return
        volume = 1 - r / self.audibility_radius
        r_vol = (dx / 2 * r + .5) * volume
        l_vol = volume - r_vol
        music.make_sound(self.cry_sound, l_vol, r_vol)


class Level(pg.Surface):
    level_num: int
    width: int
    height: int
    visible_area: RectType
    rows: int
    cols: int
    player: Optional[Player]
    tiles: List[List[Tile]]
    light_sources: Set[LightSource]

    tile_width = tile_height = 64

    def __init__(self, level_num):
        self.in_game = False

        self.level_num = level_num

        # группы спрайтов
        self.all_sprites = pg.sprite.Group()
        self.light_sprites = pg.sprite.Group()
        self.collided_sprites = pg.sprite.Group()
        self.tiles_group = pg.sprite.Group()
        self.player_group = pg.sprite.Group()
        self.enemies_group = pg.sprite.Group()
        self.objects_group = pg.sprite.Group()
        self.useable_objects_group = pg.sprite.Group()
        self.participles_group = pg.sprite.Group()

        self.light_sources = set()

        # Заполняются методом generate_level
        self.player, self.cols, self.rows = None, 0, 0
        self.width, self.height = 0, 0
        self.visible_area = pg.Rect(0, 0, 0, 0)
        self.tiles = []
        self.generate_level(self.load_level(level_num))

        super().__init__((self.width, self.height))

        self.in_game = True
        self.relight_all()

    @staticmethod
    def load_level(level_num: int) -> List[str]:
        filename = os.path.join('levels', f'l{level_num}.txt')
        # читаем уровень, убирая символы перевода строки
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]

        # и подсчитываем максимальную длину
        max_width = max(map(len, level_map))

        # дополняем каждую строку пустыми клетками ('.')
        return list(map(lambda x: x.ljust(max_width, '.'), level_map))

    def generate_level(self, level) -> None:
        self.tiles.clear()
        self.cols = 0
        self.rows = len(level)
        player_pos = (0, 0)
        for y in range(len(level)):
            self.tiles.append([])
            self.cols = max(self.cols, len(level[y]))
            for x in range(len(level[y])):
                if level[y][x] == '#':
                    tile = Tile('wall', True, x, y, self)
                else:
                    tile = Tile('empty', False, x, y, self)
                    if level[y][x] == '@':
                        player_pos = x, y
                    elif level[y][x] == '%':
                        Enemy(x, y, self)
                    elif level[y][x] == '$':
                        Exit(x, y, self)
                    elif level[y][x] == '*':
                        Torch((int(Level.tile_width * (x + .5)), int(Level.tile_height * (y + .5))),
                              self)
                self.tiles[-1].append(tile)

        self.width, self.height = Level.tile_width * self.cols, Level.tile_height * self.rows
        self.visible_area.size = self.width, self.height

        Border(pg.Rect(0, -1, self.width, 1), self)  # Верхняя граница
        Border(pg.Rect(0, self.height, self.width, 1), self)  # Нижняя
        Border(pg.Rect(-1, 0, 1, self.height), self)  # Левая
        Border(pg.Rect(self.width, 0, 1, self.height), self)  # Правая

        self.player = Player(*player_pos, self)

    def update(self, *args) -> None:
        self.all_sprites.update(*args)
        music.play('game')

    def draw_on(self, screen: pg.Surface, rect: pg.Rect) -> None:
        """Рисует все свои спрайты на себе, затем блитает на screen часть себя.
        Фокусируется на игроке, но не выходя за границы. (У краёв игрок будет не в центре)"""
        self.fill(pg.Color("black"))

        # Рисуем спрайты в определёной последовательности
        self.tiles_group.draw(self)
        self.objects_group.draw(self)
        self.enemies_group.draw(self)
        self.player_group.draw(self)
        self.participles_group.draw(self)

        # вычисляем координаты прямоугольника, который будем рисовать
        target = self.player.rect  # фокус на игроке
        self.visible_area = rect.copy()
        self.visible_area.x = max(0, min(self.width - rect.width,
                                         target.x + target.width // 2 - rect.width // 2))
        self.visible_area.y = max(0, min(self.height - rect.height,
                                         target.y + target.height // 2 - rect.height // 2))

        screen.blit(self, rect, self.visible_area)
        screen.blit(self.player.draw_inventory(), rect)

    def count_light_between(self, light_source: LightSource, target: LightedSprite) -> None:
        """Освещает target относительно light_source"""
        pos, light_power = light_source

        ray_step = 5
        light_step = 40

        # Константы для более бытрого счёта
        rs_ls = ray_step * light_step
        rs_ls2 = rs_ls ** 2
        sp_c = find_center(target)
        r = (pos[0] - sp_c[0]) ** 2 + (pos[1] - sp_c[1]) ** 2
        if r >= rs_ls2:
            return None
        r = sqrt(r)
        dl = round(light_power * (1 - r / rs_ls))
        for point in target.tracking_points:
            if self.ray_tracing(target, pos, point, r):
                target.light += dl
                break

    def count_light_for_source(self, light_source: LightSource):
        for sprite in self.light_sprites:
            self.count_light_between(light_source, sprite)

    def add_light(self, light_source: LightSource):
        self.light_sources.add(light_source)
        if running:
            self.count_light_for_source(light_source)

    def remove_light(self, light_source: LightSource):
        if light_source in self.light_sources:
            self.light_sources.remove(light_source)
        else:
            self.light_sources.add((light_source[0], -light_source[1]))

        if running:
            self.count_light_for_source((light_source[0], -light_source[1]))

    def relight_all(self) -> None:
        """Полностью перепросчитывает свет."""
        if self.in_game:
            for sprite in self.light_sprites:
                sprite.light = MINIMUM_LIGHT

            for light_source in self.light_sources:
                self.count_light_for_source(light_source)

    def relight_it(self, sprite: LightedSprite) -> None:
        """Переосвещает данный спрайт"""
        if self.in_game:
            sprite.light = MINIMUM_LIGHT
            for light_source in self.light_sources:
                self.count_light_between(light_source, sprite)

    def ray_tracing(self, target: LightedSprite, a: Point, b: Optional[Point] = None,
                    r: Optional[int] = None) -> bool:
        """Проверяет доходит ли луч от a до target."""
        if b is None:
            b = find_center(target)

        dx = b[0] - a[0]
        dy = b[1] - a[1]
        if r is None:
            r = sqrt(dx ** 2 + dy ** 2)
        if r == 0:
            return True

        m = 16  # Модификатор. Ускоряет просчёт

        r /= m
        r = ceil(r)
        dx = dx / r
        dy = dy / r
        now_cord = list(a)
        for _ in range(int(r) + 2):
            if now_cord[0] == b[0] and now_cord[1] == b[1]:
                return True
            if target.rect.collidepoint(*now_cord):
                return True

            tile = self.cords_to_tile(now_cord)
            if tile is not None:
                if tile is target:
                    return True
                if tile.is_collide:
                    return False
            now_cord[0] += dx
            now_cord[1] += dy
        return False

    def cords_to_tile(self, cords: Point) -> Optional[Tile]:
        """Возращает Tile рассположенную в данных координатах"""
        x = int(cords[0] // self.tile_width)
        y = int(cords[1] // self.tile_height)
        if (0 <= y < len(self.tiles)) and (0 <= x < len(self.tiles[y])):
            return self.tiles[y][x]
        else:
            return None

    def win(self):
        """Выводим сообщение о прохождения уровня и запускаем следующий если он существует."""
        if os.path.isfile(os.path.join('levels', f'l{self.level_num + 1}.txt')):
            win_screen(self.level_num)
            self.next_level()
        else:
            win_screen('all game')
            MainMenu()

    def next_level(self) -> None:
        """Сохраняем информацию о прохождении уровня и запускаем следующий"""
        user_data = read_saved_data()
        user_data['level'] = str(self.level_num + 1)
        save_data(user_data)
        self.__init__(self.level_num + 1)


class Cursor(pg.sprite.Sprite):
    """Класс предназначеный для замены стандартного курсора на красивый"""
    pg.mouse.set_visible(False)
    image = load_image("arrow.png")

    def __init__(self, group):
        super().__init__(group)
        self.rect = self.image.get_rect()

    def update(self):
        if pg.mouse.get_focused():
            self.rect.topleft = pg.mouse.get_pos()
        else:
            self.rect.topleft = SIZE


mouse = pg.sprite.Group()
Cursor(mouse)

music = MusicPlayer()

level = None
hello_screen()
control_screen()
MainMenu()

# Главный игровой цикл
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            terminate()
        elif event.type == pg.MOUSEBUTTONDOWN:
            pass
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                Pause()
        elif event.type == pg.KEYUP:
            level.update(event)
    level.update()

    # Рисуем уровень
    screen.fill(pg.Color("black"))
    level.draw_on(screen, pg.Rect(0, 0, WIDTH, HEIGHT))

    # Рисуем свой курсор
    mouse.update()
    mouse.draw(screen)

    pg.display.flip()

    clock.tick(FPS)
    print("\rFPS:", clock.get_fps(), end='')
