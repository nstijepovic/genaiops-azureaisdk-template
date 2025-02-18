""" A module to evaluate the length of the answer. """


class AnswerLengthEvaluator:
    """ A class to evaluate the length of the answer. """
    def __init__(self):
        pass

    # A class is made a callable my implementing the special method __call__
    def __call__(self, *, response: str, **kwargs):
        return {"answer_length": len(str(response))}
