import enum

from .utils import bc


class PlannerResult(enum.Enum):
    INVALID = enum.auto()
    PLAN_TO_GOAL = enum.auto()
    PLAN_TO_ADMISSIBLE_STATE = enum.auto()
    ALREADY_AT_GOAL = enum.auto()
    PLANNER_FAILED = enum.auto()


class Plan(list):
    def __init__(self, planner):
        self.result = PlannerResult.INVALID
        self.stats = {}
        self._planner = planner

    def pretty_str(self):
        my_repr = []
        if self.result in [PlannerResult.PLAN_TO_GOAL, PlannerResult.PLAN_TO_ADMISSIBLE_STATE]:
            if self.result == PlannerResult.PLAN_TO_GOAL:
                my_repr.append(f"{bc.GREEN}PLAN TO GOAL:{bc.ENDC}")
            elif self.result == PlannerResult.PLAN_TO_ADMISSIBLE_STATE:
                my_repr.append(f"{bc.ORANGE}PLAN TO ADMISSIBLE STATE:{bc.ENDC}")
            for p in self:
                if p[0]:
                    my_repr.append(f"{p[0].pretty_str(columns=True)}")
                    if p[1]:
                        my_repr.append(f"{bc.CYAN}{p[1]}{bc.ENDC}")
        elif self.result == PlannerResult.PLANNER_FAILED:
            my_repr.append(f"{bc.RED}PLANNER FAILED{bc.ENDC}")
        elif self.result == PlannerResult.ALREADY_AT_GOAL:
            my_repr.append(f"{bc.GREEN}CURRENT STATE SATISFIES GOAL{bc.ENDC}")
            my_repr.append(f"{self[0][0].pretty_str()}")
        return "\n".join(my_repr)

