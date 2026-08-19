from logging import debug

from streamlit.testing.v1 import AppTest


def test_hello():
    at = AppTest.from_file("../hello.py")
    at.run()

    assert at.markdown[2].value == "#### Prototype tools available"
    assert not at.exception

    # this is relative to `../hello.py`, not the test
    # at.switch_page("apps/improvement_radar/app.py")
    at.switch_page("apps/tariff_price_changes/app.py")
    at.run()

    assert not at.exception
    breakpoint()
    assert at.markdown[2].value != "#### Prototype tools available"


# def test_llm():
#     at = AppTest.from_file("../hello.py").run()
#     print("=== BEFORE SWITCH ===")
#     print("titles:", [t.value for t in at.title])
#     print("markdown:", [m.value for m in at.markdown[:5]])

#     at.switch_page("apps/tariff_price_changes/app.py")
#     at.run()
#     print("=== AFTER SWITCH ===")
#     print("titles:", [t.value for t in at.title])
#     print("markdown:", [m.value for m in at.markdown[:5]])
#     print("exception:", at.exception)


# def test_llm2():
#     at2 = AppTest.from_file("../apps/tariff_price_changes/app.py").run()
#     print("standalone titles:", [t.value for t in at2.title])
#     print("standalone markdown:", [m.value for m in at2.markdown[:5]])
#     print("standalone exception:", at2.exception)


# def test_llm3():
#     at = AppTest.from_file("../hello.py").run()
#     print(
#         "script path before:",
#         at._runner.session_state if hasattr(at, "_runner") else "n/a",
#     )

#     result = at.switch_page("apps/tariff_price_changes/app.py")
#     print("switch_page returned:", result)
#     print("same object?", result is at)

#     at.run()
