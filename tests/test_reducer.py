"""Tests for reducer utilities."""

from statequark import quark_with_reducer


class TestQuarkWithReducer:
    def test_basic_reducer(self):
        def counter_reducer(state, action):
            if action == "INC":
                return state + 1
            if action == "DEC":
                return state - 1
            return state

        counter = quark_with_reducer(0, counter_reducer)
        assert counter.value == 0

        counter.dispatch("INC")
        assert counter.value == 1

        counter.dispatch("INC")
        counter.dispatch("INC")
        assert counter.value == 3

        counter.dispatch("DEC")
        assert counter.value == 2

    def test_reducer_with_dict_action(self):
        def motor_reducer(state, action):
            match action["type"]:
                case "START":
                    return {**state, "running": True}
                case "STOP":
                    return {**state, "running": False}
                case "SET_SPEED":
                    return {**state, "speed": action["value"]}
            return state

        motor = quark_with_reducer({"running": False, "speed": 0}, motor_reducer)
        motor.dispatch({"type": "START"})
        assert motor.value["running"] is True

        motor.dispatch({"type": "SET_SPEED", "value": 100})
        assert motor.value["speed"] == 100

    def test_reducer_subscription(self):
        changes = []

        def reducer(s, a):
            return s + a

        q = quark_with_reducer(0, reducer)
        q.subscribe(lambda x: changes.append(x.value))

        q.dispatch(5)
        q.dispatch(3)
        assert changes == [5, 8]
