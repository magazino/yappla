import re
from typing import List, Dict

from .utils import bc


class Goal(list):
    """A goal is a list of dictionaries, each dictionary contains:
    * an optional "priority" (default: 10): higher priority goals are reached
      first, the lower priority goals are considered only if the current state
      satisfies the higher priority goals
    * an optional "conditions", that is either a string or a CompiledExpression,
      specifying a set of conditions that activates this particular goal (i.e.,
      if the conditions are not satisfied in the current state, the goal
      is not taken into account)
    * the actual "goal", that is either a string or a CompiledExpression over
      the state variables
    """

    def pretty_str(self, columns=True) -> str:
        if not columns:
            return str(self)
        else:
            lines = []
            self.sort(key=lambda x: -x["priority"] if "priority" in x else -10)
            for g in self:
                prio = g["priority"] if "priority" in g else 10
                cond = "[" + g["conditions"] + "]" if "conditions" in g else ""
                goal = re.sub(r" +", " ", g["goal"].replace("\n", " "))
                g = f"{bc.BOLD}{prio}{bc.ENDC} {bc.ORANGE}{cond}{bc.ENDC} {goal}"
                lines.append(str(g))
            return "\n".join(lines)
