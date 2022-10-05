import time
import copy
import logging

from .state import State
from .utils import CompiledExpression, bc, PriorityQueue
from .plan import Plan, PlannerResult


class Planner:
    def __init__(self, logger=None):
        self.max_iterations = 10000
        self._cur_goal = None
        self._domain = None
        self.verbosity_level = 0  # 0 no messages, 1 only a few, 2 everything
        if not logger:
            console = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)-8s:%(name)-12s: %(message)s")
            console.setFormatter(formatter)
            logger = logging.getLogger("MagPlanner")
            logger.addHandler(console)
        self.logger = logger

    def set_domain(self, domain):
        self._domain = domain

    @property
    def domain(self):
        return self._domain

    def plan(self, initial_state: "State", goal=None):
        if goal:
            self.set_goal(goal)
        initial_time = time.thread_time()
        initial_state = State(copy.deepcopy(initial_state))
        cur_goal_str = self._compute_cur_goal(initial_state)
        cur_goal_expr = CompiledExpression(cur_goal_str)
        initial_state_satisfies_constraints = True
        #initial_state.satisfies_constraints(
        #    self._domain.constraints
        #)
        self._print(1, "")
        if not initial_state_satisfies_constraints:
            self._print(
                2,
                f"{bc.ORANGE}Constraints violated! The goal will be to return to the closest acceptable state{bc.ENDC}",
            )
        self._print(1, f"Planning from state: {initial_state.pretty_str()}")
        self._print(1, f"To goal: {cur_goal_str}")
        open_pq = PriorityQueue()
        open_pq.push(initial_state, 0)  # state descriptions are taken from here
        to_reach = [
            (None, None, initial_state)
        ]  # contains tuples (prev_state, action, new_state), to_reach also needs full states to reconstruct the plan
        visited = []
        plan = Plan(self)
        planning_iterations = 0
        while planning_iterations < self.max_iterations:
            # choose the state we expand from
            if open_pq.empty():
                break
            state, cur_state_cost = open_pq.pop()
            visited.append(state)
            planning_iterations += 1
            if self.verbosity_level == 2:
                self._print(
                    2, f"Planning: expanding from state: {state.pretty_str()}"
                )
            elif self.verbosity_level == 1:
                print(".", end="")

            # let's decide if we reached the current goal
            goal_reached = False
            if not initial_state_satisfies_constraints:
                #goal_reached = state.satisfies_constraints(self._domain.constraints)
                pass
            else:
                goal_reached = cur_goal_expr.eval_in_state(state)

            # if we reached the goal, we compute the plan and exit the planning loop
            if goal_reached:
                if self.verbosity_level == 1:
                    print(f"[{planning_iterations}]")
                if not initial_state_satisfies_constraints:
                    self._print(
                        1,
                        f"{bc.BOLD}{bc.ORANGE}=== FOUND A PLAN TO RESTORE A LEGAL STATE ==={bc.ENDC}",
                    )
                else:
                    self._print(
                        1, f"{bc.BOLD}{bc.GREEN}=== FOUND A PLAN TO GOAL ==={bc.ENDC}"
                    )
                # compute the plan by starting from the goal backward to the initial state
                plan.append((state, None))  # this is the (goal state, no action)
                while state:
                    for ss in to_reach:
                        if ss[2] == state:
                            if ss[0]:
                                # (current state, action to perform)
                                plan.append((ss[0], ss[1]))
                            state = ss[0]
                            break  # I expect only one matching in to_reach
                plan.reverse()
                break

            # expand the state extracted from the priority queue
            for action in self._domain.actions.values():
                applicable = action.applicable(state)
                if applicable:
                    new_states = action.possible_outcomes(state, self.verbosity_level == 2)
                    for new_state in new_states:
                        if new_state in visited:
                            continue
                        #if initial_state_satisfies_constraints and not new_state.satisfies_constraints(self._domain.constraints):
                            # TODO for debugging purposes it is better to show these states in the logs
                            continue
                        if new_state in open_pq:
                            # the state was already in the open queue,
                            # if this cost is better, we should update
                            # the open queue and the to_reach list
                            old_cost = open_pq.get_value(new_state)
                            new_cost = cur_state_cost + action.cost
                            if new_cost < old_cost:
                                open_pq.update_value(new_state, new_cost)
                                idx_in_to_reach = [i for i, v in enumerate(to_reach) if v[2] == new_state][0]
                                to_reach[idx_in_to_reach] = (state, action.name, new_state)
                        else:
                            open_pq.push(new_state, cur_state_cost + action.cost)
                            to_reach.append((state, action.name, new_state))
                else:
                    self._print(
                        3, f"Action action {bc.CYAN}{action.name}{bc.ENDC} not applicable"
                    )
            if self.verbosity_level == 2:
                self._print(2, "")

        self._print(1, f"Iterations: {planning_iterations}")
        self._print(1, f"Planning time: {(time.thread_time() - initial_time) * 1000.0:.3f} milliseconds")
        if len(plan) == 0:
            self._print(1, f"{bc.ORANGE}Cannot find a plan{bc.ENDC}")
            plan.result = PlannerResult.PLANNER_FAILED
        elif len(plan) == 1:
            self._print(1, f"{bc.BOLD}{bc.GREEN}=== ALREADY AT GOAL!!! ==={bc.ENDC}")
            plan.result = PlannerResult.ALREADY_AT_GOAL
        else:
            if initial_state_satisfies_constraints:
                plan.result = PlannerResult.PLAN_TO_GOAL
            else:
                plan.result = PlannerResult.PLAN_TO_ADMISSIBLE_STATE
            self._print(1, f"{bc.BOLD}{bc.GREEN}=== PLAN: ==={bc.ENDC}")
            self._print(1, f"{plan.pretty_str()}")

        plan.stats = {
            "time": time.thread_time() - initial_time,
            "iterations": planning_iterations,
        }
        return plan

    def set_goal(self, goal):
        self._cur_goal = {"goal": goal.replace("\n", " ")}

    def _print(self, level, message):
        if level <= self.verbosity_level:
            self.logger.info(message)

    def _compute_cur_goal(self, cur_state):
        return self._cur_goal["goal"]

    def apply_action_to_state(self, action_name, state):
        return self._domain.actions[action_name].apply(state)

