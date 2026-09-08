class Game:
    def __init__(self):
        self._init_hooks = []
        self._update_hooks = []
        self._draw_hooks = []
        self._input_hooks = []

    def init(self, func):
        self._init_hooks.append(func)
        return func

    def update(self, func):
        self._update_hooks.append(func)
        return func

    def draw(self, func):
        self._draw_hooks.append(func)
        return func

    def input(self, func):
        self._input_hooks.append(func)
        return func

    def run_init(self):
        for hook in self._init_hooks:
            hook()

    def run_update(self):
        for hook in self._update_hooks:
            hook()

    def run_draw(self, screen):
        for hook in self._draw_hooks:
            hook(screen)

    def run_input(self, event):
        for hook in self._input_hooks:
            hook(event)


game = Game()
