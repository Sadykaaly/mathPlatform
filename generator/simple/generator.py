from sympy import symbols
import random

from generator.generator import Generator

x, y, z, u = symbols('x y z u')


class SimpleMath(Generator):

    def __str__(self):
        return self.__name__

    def generate_expression(self):
        questions = [
            f'{self.a} + {self.b}',
            f'{self.a}*{self.b}',
            f'{self.a}+(-{self.b})',
            f'{self.a}/{self.b}',
            f'({self.a}+{self.b})+{self.c}',
            f'{self.a} - {self.b}',
            f'{self.a} + {self.b} - {self.c}'
        ]

        expression = random.choice(questions)
        return expression

    def solve(self, expression):
        precision = "{:.2f}"
        return precision.format(eval(expression))

    def question_and_solution(self):
        question = self.generate_expression()
        result = dict(
            question=question,
            answer=self.solve(question)
        )
        return result
