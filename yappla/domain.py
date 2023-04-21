from typing import Dict

from yappla import Action
from yappla import StateVariable
from yappla import State


class Domain:
    """ A domain contains the definition of the state variables and the actions. """

    def __init__(self):
        self._actions = {}
        self._variables = {}

    def action(self, name) -> Action:
        return self._actions.get(name, None)

    @property
    def actions(self) -> Dict[str, Action]:
        return self._actions

    def add_action(self, action: Action):
        self._actions[action.name] = action

    def variable(self, name) -> StateVariable:
        return self._variables.get(name, None)

    @property
    def variables(self) -> Dict[str, StateVariable]:
        return self._variables

    def add_variable(self, variable: StateVariable):
        self._variables[variable.name] = variable

    def get_initial_state(self) -> "State":
        """This function provides the initial state, built by the initial_values
           of all the state variables."""
        return State(
            {
                name: definition.initial_value if definition.initial_value is not None else "UNK"
                for name, definition in self._variables.items()
            }
        )

    def load_from_dict(self, definition):
        if "domain" in definition:
            definition = definition["domain"]
        for action_name, action_definition in definition["actions"].items():
            yaction = Action(name=action_name, **action_definition)
            self.add_action(yaction)
        for variable_name, variable_definition in definition["variables"].items():
            yvariable = StateVariable(name=variable_name, **variable_definition)
            self.add_variable(yvariable)

