import time
import copy
import logging

from .state import State
from .utils import CompiledExpression, bc, PriorityQueue
from .plan import Plan, PlannerOutcome, PlannerResult


class Planner:
    class FakePrintLogger:
        def info(self, message):
            print("[YAPPLA] " + message)

    def __init__(self, logger=None):
        self.max_iterations = 10000
        self._cur_goal = None
        self._domain = None
        self.max_verbosity_level = 0  # 0 no messages, 1 only a few, 2 everything
        if not logger:
            #console = logging.StreamHandler()
            #formatter = logging.Formatter("%(levelname)-8s:%(name)-12s: %(message)s")
            #console.setFormatter(formatter)
            #logger = logging.getLogger("MagPlanner")
            #logger.addHandler(console)
            logger = Planner.FakePrintLogger()
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
        self.log(1, "")
        self.log(1, f"Planning from state: [{initial_state.hash()}]\n{initial_state.pretty_str()}")
        self.log(1, f"To goal: {cur_goal_str}")
        open_pq = PriorityQueue()
        open_pq.push(initial_state, 0)  # state descriptions are taken from here
        to_reach = [
            (None, None, initial_state)
        ]  # contains tuples (prev_state, action, new_state), to_reach also needs full states to reconstruct the plan
        visited = []
        planner_result = PlannerResult(self)
        planning_iterations = 0
        while planning_iterations < self.max_iterations:
            # choose the state we expand from
            if open_pq.empty():
                break
            state, cur_state_cost = open_pq.pop()
            visited.append(state)
            planning_iterations += 1
            if self.max_verbosity_level >= 2:
                self.log(
                    2, f"(O) [{state.hash()}] cost={cur_state_cost}\n{state.pretty_str()}"
                )
            elif self.max_verbosity_level == 1:
                print(".", end="")

            # let's decide if we reached the current goal
            goal_reached = cur_goal_expr.eval_in_state(state)

            # if we reached the goal, we compute the plan and exit the planning loop
            if goal_reached:
                if self.max_verbosity_level == 1:
                    self.log(1, f"[{planning_iterations}]")
                self.log(
                    1, f"{bc.BOLD}{bc.GREEN}=== FOUND A PLAN TO GOAL ==={bc.ENDC}"
                )

                plan = Plan()
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
                planner_result.plan = plan
                break

            # expand the state extracted from the priority queue
            for action in self._domain.actions.values():
                applicable = action.applicable(state)
                if applicable:
                    new_states = action.possible_outcomes(state) #, self.max_verbosity_level == 3)
                    for new_state in new_states:
                        self.log(3, f"[{state.hash()}] -- {bc.CYAN}{action.name}{bc.ENDC} ({action.cost}) -> [{new_state.hash()}]\n{new_state.pretty_str()}")
                        if new_state in visited:
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
                    self.log(
                        3, f"{bc.CYAN}{action.name}{bc.ENDC} not applicable"
                    )
            if self.max_verbosity_level == 2:
                self.log(2, "")

        self.log(1, f"Iterations: {planning_iterations}")
        self.log(1, f"Planning time: {(time.thread_time() - initial_time) * 1000.0:.3f} milliseconds")
        if planner_result.plan is None:
            self.log(1, f"{bc.ORANGE}Cannot find a plan{bc.ENDC}")
            planner_result.outcome = PlannerOutcome.FAILURE
        elif len(planner_result.plan) == 1:
            self.log(1, f"{bc.BOLD}{bc.GREEN}=== ALREADY AT GOAL!!! ==={bc.ENDC}")
            planner_result.outcome = PlannerOutcome.ALREADY_AT_GOAL
        else:
            planner_result.outcome = PlannerOutcome.SUCCESS
            self.log(1, f"{bc.BOLD}{bc.GREEN}=== PLAN: ==={bc.ENDC}")
            self.log(1, f"{planner_result.pretty_str(True)}")

        planner_result.stats = {
            "time": time.thread_time() - initial_time,
            "iterations": planning_iterations,
        }
        return planner_result

    def set_goal(self, goal):
        self._cur_goal = {"goal": goal.replace("\n", " ")}

    def log(self, level, message):
        if level <= self.max_verbosity_level:
            self.logger.info(message)

    def _compute_cur_goal(self, cur_state):
        return self._cur_goal["goal"]

    def apply_action_to_state(self, action_name, state):
        return self._domain.actions[action_name].apply(state)

