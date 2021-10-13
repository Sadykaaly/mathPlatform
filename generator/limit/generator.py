from sympy import symbols, Limit, exp, oo, cos, sin, sqrt
import random

from generator.generator import Generator

x, y, z, u = symbols('x y z u')


class LimitGenerator(Generator):
    def __str__(self):
        return self.__name__

    def generate_expression(self):
        questions = [Limit(self.a / x, x, 0, '-'),
                     Limit(x ** 2 / exp(x), x, 0),
                     Limit(x / (self.a * x - self.b), x, oo),
                     Limit((self.a * x ** 3 - self.b * x ** 2 + self.c) / (self.d + self.e * x - self.f * x ** 3), x, oo),
                     Limit((x ** 2 - self.a) / (x - x ** 2), x, oo, '-'),
                     Limit((x ** 2 + self.a) / (x ** 3 + self.b), x, oo, '-'),
                     Limit((x ** 2 + sin(x)) / (x ** 2 + cos(x)), x, oo),
                     Limit((self.a * x + 2 * sqrt(x)) / (self.b - x), x, oo),
                     Limit((self.a * x - self.c) / sqrt(self.b * x ** 2 + x + self.c), x, oo),
                     Limit((self.a * x - self.b) / sqrt(self.c * x ** 2 + x + self.d), x, oo, '-'),
                     Limit((self.a * x - self.b) / abs(self.c * x + self.d), x, oo, '-'),
                     Limit(self.a / (self.b - x), x, self.c),
                     Limit(self.a / (self.b - x) ** 2, x, self.c),
                     Limit(self.a / (self.b - x), x, self.c, '-'),
                     Limit(self.a / (self.b - x), x, self.c, '+'),
                     Limit((self.a * x + self.b) / (self.c * x + self.d), x, -self.e / self.f, '-'),
                     Limit((self.a * x + self.b) / (self.c * x + self.d), x, -self.e / self.f, '+'),
                     Limit(x / (self.a - x) ** 3, x, self.b, '+'),
                     Limit(x / sqrt(self.a + x ** 2), x, self.b, '-'),
                     Limit(x / sqrt(self.a - x ** 2), x, self.b, '+'),
                     ]
        expression = random.choice(questions)
        return expression

    def solve(self, expression):
        return expression.doit()

    def question_and_solution(self):
        question = self.generate_expression()
        result = dict(
            question=question,
            answer=self.solve(question)
        )
        return result