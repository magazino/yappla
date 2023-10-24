import enum

from .utils import bc


class PlannerOutcome(enum.Enum):
    INVALID = enum.auto()
    SUCCESS = enum.auto()
    ALREADY_AT_GOAL = enum.auto()
    FAILURE = enum.auto()


def _diff_dicts(a, b, missing=KeyError):
    return {
        key: (a.get(key, missing), b.get(key, missing))
        for key in dict(set(a.items()) ^ set(b.items())).keys()
    }


class PlannerResult:
    def __init__(self, planner):
        self.outcome = PlannerOutcome.INVALID
        self.plan = None
        self.stats = {}
        self._planner = planner

    def pretty_str(self, show_state_hashes=False, only_diffs=False):
        my_repr = []
        if self.outcome in [PlannerOutcome.SUCCESS]:
            my_repr.append(f"{bc.GREEN}PLAN TO GOAL:{bc.ENDC}")
            prev_state = None
            for p in self.plan:
                if p[0]:
                    if not only_diffs:
                        my_repr.append(f"{p[0].pretty_str(columns=True, show_hashes=show_state_hashes, diff_with=prev_state)}")
                    else:
                        my_repr.append(f"{p[0].pretty_str(columns=True, show_hashes=show_state_hashes)}")
                if p[1]:
                    my_repr.append(f"{bc.CYAN}{p[1]}{bc.ENDC}")
                prev_state = p[0]
        elif self.outcome == PlannerOutcome.FAILURE:
            my_repr.append(f"{bc.RED}PLANNER FAILED{bc.ENDC}")
        elif self.outcome == PlannerOutcome.ALREADY_AT_GOAL:
            my_repr.append(f"{bc.GREEN}CURRENT STATE SATISFIES GOAL{bc.ENDC}")
            my_repr.append(f"{self.plan[0][0].pretty_str()}")
        return "\n".join(my_repr)


class Plan(list):
    pass

