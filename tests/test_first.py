import pytest
from streamlit.testing.v1 import AppTest


def test_hello():
    at = AppTest.from_file("../hello.py").run()

    assert at.markdown[2].value == "#### Prototype tools available"
    assert not at.exception


@pytest.fixture
def app_loader():
    def load(app_name):
        at = AppTest.from_file("../hello.py").run()

        # this is relative to `../hello.py`, not the test
        # at.switch_page("apps/improvement_radar/app.py")
        # Nb. with default timeout=3s this was intermittently failing
        at.switch_page(f"apps/{app_name}/app.py").run(timeout=10)

        return at

    return load


def test_tariff_price_changes(app_loader):

    at = app_loader("tariff_price_changes")

    assert not at.exception
    assert (
        at.info[1].value
        == "#### Total estimated monthly price difference for July 2026: £7,964,130"
    )


def test_prescribing_topx(app_loader):
    at = app_loader("prescribing_topx")

    assert not at.exception

    assert at.expander[0].label == "Tirzepatide — £189,476,111.06 (833,852 items)"
    assert (
        at.dataframe[0].value.iat[0, 0]
        == "Mounjaro KwikPen 5mg/0.6ml solution for injection 2.4ml pre-filled pens (Eli Lilly and Company Ltd)"
    )
    assert at.dataframe[0].value.iat[0, 1] == "£54,222,327.98"


def test_measure_aware(app_loader):
    at = app_loader("measure_aware")

    assert not at.exception

    assert str(at.dataframe[0].value.iat[0, 0]) == "2025-10-01 00:00:00"
    assert at.dataframe[0].value.iat[0, 1] == "icb"
    assert at.dataframe[0].value.iat[0, 3] == pytest.approx(0.17135061878098362)
