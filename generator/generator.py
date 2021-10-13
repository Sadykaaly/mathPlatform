import random


class Generator:
    """
    Base class for all generator types.
    Shared properties placed here.
    """

    SIMPLE = 'simple'
    LIMIT = 'limit'
    INTEGRAL = 'integral'

    GENERATOR_TYPE = (
        (SIMPLE, 'Simple'),
        (LIMIT, 'Limit'),
        (INTEGRAL, 'Integral')
    )

    GENERATOR_TYPES_LIST = [SIMPLE, LIMIT, INTEGRAL]

    def __init__(self):
        self.a = int(random.randint(1, 15))
        self.b = int(random.randint(1, 15))
        self.c = int(random.randint(1, 15))
        self.d = int(random.randint(1, 15))
        self.e = int(random.randint(1, 15))
        self.f = int(random.randint(1, 15))

    def __str__(self):
        return self.__name__

    @classmethod
    def get_generator(cls, theme):
        from generator.integral.generator import IntegralGenerator
        from generator.limit.generator import LimitGenerator
        from generator.simple.generator import SimpleMath

        GENERATORS = {
            cls.SIMPLE: SimpleMath,
            cls.LIMIT: LimitGenerator,
            cls.INTEGRAL: IntegralGenerator,
        }
        print(theme)
        print(GENERATORS)
        return GENERATORS[theme]