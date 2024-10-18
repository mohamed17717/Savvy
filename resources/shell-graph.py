import cProfile


def c(func):
    p = cProfile.Profile()
    p.enable()
    func()
    p.print_stats("cumtime")
    p.disable()
