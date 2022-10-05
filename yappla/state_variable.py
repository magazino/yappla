
class StateVariable:
    def __init__(self, name, values, initial_value=None, possible_values=None, type=None):
        self.name = name
        self.values = values
        self.initial_value = initial_value
        self.var_type = type
        # FIXME remove values, possible_values is the one that should be kept
        self.possible_values = possible_values

    def __repr__(self):
        return f"VARIABLE {self.name} [{', '.join(self.values)}] initial = {self.initial_value}"
