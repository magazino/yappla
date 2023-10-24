import hashlib
import base64
from typing import Dict, List, Union

from .utils import bc, eval_expression


class State(dict):
    """A State is a dictionary encoding a possible state of the system, that is
    a particular (complete) assignment of all the state variables (the state
    dict is a mapping state variable name (str) -> value (str)).
    """
    _COLS = 200 #os.get_terminal_size().columns

    def satisfies_constraints(self, constraints: List[Dict]) -> bool:
        """Evaluates if this state satisfies the constraints.

        The constraints is a list of dicts, each containing a "conditions" that
        activates the constraints (i.e. the constraint is not checked if the
        conditions are not satisfied by this state) and the actual "costraint".
        Both the values of "conditions" and "constraint" can be either a string
        or a CompiledExpression.
        """
        for c in constraints:
            if eval_expression(c["conditions"], self) and not eval_expression(
                c["constraint"], self
            ):
                return False
        return True

    def satisfies_conditions(self, conditions: Union[str, "CompiledExpression"]) -> bool:
        """Evaluates the conditions over this state.

        This function returns True if conditions are met (i.e. if the condition
        expression evaluates to True in this state), False otherwise.
        """
        return eval_expression(conditions, self)

    def pretty_str(self, columns: bool = True, show_hashes: bool = False, diff_with: "State" = None) -> str:
        if not columns:
            if show_hashes:
                return f"[{self.hash()}] " + ", ".join([f"{bc.BOLD}{k}{bc.ENDC}:{v}" for k, v in self.items()])
            else:
                return ", ".join([f"{bc.BOLD}{k}{bc.ENDC}:{v}" for k, v in self.items()])
        else:
            sv0 = [(k, v) for k, v in self.items() if not k.endswith("__state")]
            sv1 = list(self.items() - sv0)
            sv0.sort(key=lambda x: x[0])
            sv1.sort(key=lambda x: x[0])
            lines = []
            line = []
            linelen = 0
            for items in [sv0, sv1]:
                for k, v in items:
                    reclen = len(k) + len(str(v)) + 1 + 2
                    if linelen + reclen > State._COLS:
                        lines.append(line)
                        line = []
                        linelen = 0
                    line.append(f"{bc.BOLD}{k}{bc.ENDC}:{v}")
                    linelen += reclen
                lines.append(line)
                line = []
                linelen = 0
            for i in range(len(lines)):
                lines[i] = ', '.join(lines[i])

            if show_hashes:
                return f"[{self.hash()}] " + "\n".join(lines)
            else:
                return "\n".join(lines)

    def hash(self):
        h = hashlib.md5()
        h.update(str(frozenset(self.items())).encode("ascii"))
        return h.hexdigest()[-6:]
