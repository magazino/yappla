from typing import List, Union, Dict

from .utils import bc, eval_expression
from .state import State


class Action:
    """This class model a action operator, i.e. an operator that can be
    applied to a planning state and result in another (set of) state(s).

    We can think of an action operator as the low-level operative version of an action
    representation.

    During the definition of a domain, durative actions are split into
    a set of action operators (start, end, abort, aborted) to ease the
    planning process.
    """

    def __init__(
        self, name: str, preconditions: str = "", effects: Union[List, Dict] = None, cost: int = 10
    ):
        """Constructor

        Args:
            name (str): the name of the operator
            preconditions (str): an expression specifying the preconditions that
                have to hold to apply this operator
            effects (list): a list of dicts containing the (expected) effects of the
                application of this operator, for each variable name, the
                dict contains either a string with the expected value or
                a list of strings in case of multiple possible effects
            cost (int): this is the cost of applying this operator, e.g., for
                better modeling the differences between aborting or ending
                an action
        """
        self.name = name
        self._preconditions = preconditions
        if effects is None:
            self._effects = None
        elif isinstance(effects, list):
            self._effects = effects
        elif isinstance(effects, dict):
            self._effects = [effects]
        self.cost = cost

    def __repr__(self) -> str:
        return (
            "ACTION "
            + self.name
            + " {\n"
            + "  preconditions:\n"
            + "    " + str(self._preconditions) + "\n"
            + "  effects:\n"
            + "    " + str(self._effects) + "\n"
            + "  cost: " + str(self.cost) + "\n"
            + "}"
        )

    @property
    def preconditions(self) -> str:
        """Get the (pre-)preconditions for this operator."""
        return self._preconditions

    @property
    def effects(self) -> list:
        """Get the effects of this operator."""
        return self._effects

    def applicable(self, state: "State") -> bool:
        """Returns True if the operator can be applied in the state `state`."""
        return eval_expression(self._preconditions, state)

    def possible_outcomes(self, state: "State", verbose: bool = False) -> List[State]:
        """Returns a list of possible states that would result by applying
        the operator to the state provided as parameter.
        """
        state = State(state)
        eff = self.effects
        new_states = []
        if verbose:
            print(f"Applying action operator {bc.CYAN}{self.name}{bc.ENDC} with effects {eff}")
            print(f"  (O) {state.pretty_str()}")
        for e in eff:
            new_state = State({**state, **e})
            if verbose:
                print(f"  --> {new_state.pretty_str()}")
            new_states.append(new_state)
        return new_states

    def apply(self, state: "State", verbose: bool = False):
        """Apply the operator to the state `state` and returns the resulting
        state. In case multiple states are possible, the value of the
        non deterministic state variables is set to the special value "?".
        """
        new_states = self.possible_outcomes(state, verbose)
        if len(new_states) == 1:
            return new_states[0]
        else:
            new_state = state
            vars_in_state = new_states[0].keys()
            for v in vars_in_state:
                vals = set([s[v] for s in new_states])
                if len(vals) == 1:
                    new_state[v] = vals.pop()
                else:
                    new_state[v] = "?"
            return new_state
