import cmbagent


def test_one_shot_engineer_oss():

    task = r"""
    Compute the sum of the first 1000 natural numbers.
    Plot the histogram of the numbers.
    """

    task = r"""
    Analyse /Users/boris/Desktop/data/Stocks.csv file using pandas.
    and then plot relevant statistics with matplotlib.
    """

    results = cmbagent.one_shot(
        task,
        max_rounds=25,
        max_n_attempts=10,
        agent="engineer",
        engineer_model="gpt-oss-120b",
        default_formatter_model="gpt-oss-120b",
        default_llm_model="gpt-oss-120b",
        work_dir="/Users/boris/Desktop/one_shot_engineer_oss",
        clear_work_dir=True,
    )

    assert results is not None


test_one_shot_engineer_oss()
