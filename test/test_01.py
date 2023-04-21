import yappla
from yappla.plan import PlannerOutcome


def test_feet_shoes():
    initial_state = yappla.State({"left_foot": "has_nothing", "right_foot": "has_nothing"})
    put_left_sock = yappla.Action(
        "put_left_sock",
        preconditions="left_foot == 'has_nothing'",
        effects=[{"left_foot": "has_sock"}])
    put_right_sock = yappla.Action(
        "put_right_sock",
        preconditions="right_foot == 'has_nothing'",
        effects=[{"right_foot": "has_sock"}])
    put_left_shoe = yappla.Action(
        "put_left_shoe",
        preconditions="left_foot == 'has_sock'",
        effects=[{"left_foot": "has_shoe"}])
    put_right_shoe = yappla.Action(
        "put_right_shoe",
        preconditions="right_foot == 'has_sock'",
        effects=[{"right_foot": "has_shoe"}])

    domain = yappla.Domain()
    domain.add_action(put_left_sock)
    domain.add_action(put_right_sock)
    domain.add_action(put_left_shoe)
    domain.add_action(put_right_shoe)

    #goal = yappla.Goal()
    #goal.append({"goal": "left_foot == 'has_shoe' and right_foot == 'has_shoe'"})
    goal = "left_foot == 'has_shoe' and right_foot == 'has_shoe'"

    planner = yappla.Planner()
    planner.set_domain(domain)
    planner_result = planner.plan(initial_state, goal)

    assert planner_result.outcome == PlannerOutcome.SUCCESS
    assert len(planner_result.plan) == 5  # 4 actions + the final goal state without actions
