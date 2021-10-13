from sympy import symbols, Limit, exp, oo, cos, sin, sqrt
import random

from generator.generator import Generator

x, y, z, u = symbols('x y z u')


class IntegralGenerator(Generator):

    def __str__(self):
        return self.__name__

    def generate_expression(self):
        questions = [self.a,
                     self.b * x ** 2,
                     sqrt(self.a * x),
                     x ** self.b,
                     x ** self.d,
                     (self.a * x + cos(self.b * x)),
                     self.a ** 2 - self.c * x ** 2,
                     self.a + self.b * x + self.c * x ** 2,
                     self.d * x ** (1 / 2) + self.b * x ** (1 / 3),
                     (x - self.b) / x,
                     self.b * x ** 3 / self.a - self.e * x ** 2 / self.c + self.a * x - self.b,
                     self.a + x ** self.b + x ** self.c + x ** self.d + x ** self.e,
                     cos(self.b * x),
                     sin(x / self.a),
                     1 / (self.d + x * self.c) ** 2,
                     sqrt(self.a * x + self.b),
                     self.d / (sqrt(self.a * x + self.c)),
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
