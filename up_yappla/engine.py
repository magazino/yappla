# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from typing import Optional, Callable, IO, List
import unified_planning as up
import unified_planning.engines as engines

from yappla import (
    Planner as YPlanner,
    State as YState,
    Action as YAction,
    Domain as YDomain
)


class SequentialPlanWithExpectedStates(up.plans.SequentialPlan):
    def __init__(self, expected_states, actions, environment=None):
        super().__init__(actions, environment)
        self._expected_states = expected_states


class EngineImpl(engines.Engine, engines.mixins.OneshotPlannerMixin):
    def __init__(self, **options):
        engines.Engine.__init__(self)
        engines.mixins.OneshotPlannerMixin.__init__(self)
        self._planners = {}
        self._fluent_value_replacements = {}
        if len(options) > 0:
            raise up.exceptions.UPUsageError('Custom options not supported!')

    @property
    def name(self) -> str:
        return "YAPPLA"

    def _get_nary_expression_string(self, op: str, args: List["FNode"]) -> str:
        p = []
        if len(args) > 0:
            p.append("(")
            p.append(self._fnode_to_python_expression(args[0]))
            for x in args[1:]:
                p.append(op)
                p.append(self._fnode_to_python_expression(x))
            p.append(")")
        return "".join(p)

    def _get_nary_function_parameters(self, op: str, args: List["FNode"]) -> str:
        p = []
        if len(args) > 0:
            p.append("_C_")
            p.append(self._fnode_to_python_expression(args[0]))
            for x in args[1:]:
                p.append(op)
                p.append(self._fnode_to_python_expression(x))
            p.append("_D_")
        return "".join(p)

    def _fnode_to_python_expression(self, fnode):
        if isinstance(fnode, up.model.Fluent):
            # FIXME this is a hack, we get Fluents here, because we are also
            # getting fluents_defaults, where keys are fluents, not grounded fluents
            # UP (ungrounded) fluents to Python variable names
            return fnode.name
        elif fnode.is_bool_constant():
            # UP booleans to Python booleans
            return "True" if fnode.is_true() else "False"
        elif fnode.is_int_constant():
            return str(fnode.constant_value())
        elif fnode.is_real_constant():
            return str(fnode.constant_value())
        elif fnode.is_fluent_exp():
            # UP fluent expressions to Python variable names
            return fnode.fluent().name + self._get_nary_function_parameters("_c_", fnode.args)
        elif fnode.is_parameter_exp():
            return fnode.parameter().name
        elif fnode.is_variable_exp():
            return fnode.variable().name
        elif fnode.is_object_exp():
            # UP objects to Python strings
            tp = fnode.object().type.name.replace("_type", "")
            nm = fnode.object().name.replace(tp + "_", "")
            return '"' + nm + '"'
        elif fnode.is_and():
            return self._get_nary_expression_string(" and ", fnode.args)
        elif fnode.is_or():
            return self._get_nary_expression_string(" or ", fnode.args)
        elif fnode.is_not():
            return "(not " + self._fnode_to_python_expression(fnode.arg(0)) + ")"
        elif fnode.is_equals():
            return self._fnode_to_python_expression(fnode.arg(0)) + " == " + self._fnode_to_python_expression(fnode.arg(1))
        else:
            raise Exception(f"Unsupported fnode: {type(fnode)} {fnode}")

    def _solve(self, problem: 'up.model.AbstractProblem',
               callback: Optional[Callable[['engines.PlanGenerationResult'], None]] = None,
               heuristic: Optional[Callable[["up.model.state.ROState"], Optional[float]]] = None,
               timeout: Optional[float] = None,
               output_stream: Optional[IO[str]] = None) -> 'engines.results.PlanGenerationResult':

        quality_metric = None
        if len(problem.quality_metrics) > 0 and isinstance(problem.quality_metrics[0], up.model.metrics.MinimizeActionCosts):
            quality_metric = problem.quality_metrics[0]

        if problem.name not in self._planners:
            # in YAPPLA fluents can be either Python booleans or strings
            fluent_value_replacements = {"true": "True", "false": "False"}

            # create string replacements for all user types
            for ut in problem.user_types:
                objects = problem.objects(ut)
                for obj in objects:
                    obj_name = obj.name
                    ut_prefix = ut.name.replace("_type", "_")
                    fluent_value_replacements[obj_name] = '"' + obj_name.replace(ut_prefix, "") + '"'

            # convert the actions (preconditions and effects) and them to
            # the YAPPLA domain
            ydomain = YDomain()
            for a in problem.actions:
                yprecond = up.shortcuts.And(a.preconditions)
                yprecond = self._fnode_to_python_expression(yprecond)

                yeffect = {}
                for e in a.effects:
                    yeffect[self._fnode_to_python_expression(e.fluent)] = eval(fluent_value_replacements[str(e.value)])

                yaction = YAction(name=a.name, preconditions=yprecond, effects=[yeffect])
                yaction.cost = quality_metric.get_action_cost(a).constant_value()
                print("ACTION", yaction)
                ydomain.add_action(yaction)

            yplanner = YPlanner()
            #yplanner.verbosity_level = 2
            yplanner.set_domain(ydomain)
            self._planners[problem.name] = yplanner
            self._fluent_value_replacements[problem.name] = fluent_value_replacements

        yplanner = self._planners[problem.name]
        fluent_value_replacements = self._fluent_value_replacements[problem.name]

        # create the initial state
        init_ystate = YState()
        for key, val in {**problem.fluents_defaults, **problem.initial_values}.items():
            key = self._fnode_to_python_expression(key)
            init_ystate[key] = eval(fluent_value_replacements[str(val)])

        # generate plan
        print("CURRENT GOAL", problem.goals[0])
        ygoal = self._fnode_to_python_expression(problem.goals[0])
        #ygoal = CompiledExpression(ygoal)
        planner_result = yplanner.plan(init_ystate, ygoal)

        # convert the YAPPLA result to UP result
        res = engines.PlanGenerationResultStatus.UNSOLVABLE_PROVEN if planner_result.plan is None else engines.PlanGenerationResultStatus.SOLVED_SATISFICING
        expected_state_list, action_list = zip(*planner_result.plan)
        action_list = [up.plans.ActionInstance(problem.action(action_name)) for action_name in action_list if action_name is not None]
        plan = SequentialPlanWithExpectedStates(expected_state_list, action_list)
        ret = engines.PlanGenerationResult(res, plan, self.name)
        ret.metrics = {"stats": planner_result.stats}
        return ret

    @staticmethod
    def supported_kind() -> up.model.ProblemKind:
        supported_kind = up.model.ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED') # type: ignore
        supported_kind.set_typing('FLAT_TYPING') # type: ignore
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('EQUALITY') # type: ignore
        supported_kind.set_fluents_type('OBJECT_FLUENTS') # type: ignore
        return supported_kind

    @staticmethod
    def supports(problem_kind: 'up.model.ProblemKind') -> bool:
        return problem_kind <= EngineImpl.supported_kind()

    @staticmethod
    def supports_plan(plan_kind: 'up.plans.PlanKind') -> bool:
        return plan_kind in [up.plans.PlanKind.SEQUENTIAL_PLAN, up.plans.PlanKind.TIME_TRIGGERED_PLAN]

