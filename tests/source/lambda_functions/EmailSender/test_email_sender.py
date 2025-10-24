from EmailSender.index import (
    get_subject_by_env,
)


def test_prod_subject_does_not_contain_env():
    subject = "subject line"
    enviornment = "PROD"
    correct_subject = subject
    assert get_subject_by_env(subject, enviornment) == correct_subject


def test_test_subject_contains_env():
    subject = "subject line"
    enviornment = "TEST"
    correct_subject = f"[{enviornment}] {subject}"
    assert get_subject_by_env(subject, enviornment) == correct_subject


def test_no_enviornment_contains_na():
    subject = "subject line"
    enviornment = "N/A"
    correct_subject = f"[{enviornment}] {subject}"
    assert get_subject_by_env(subject, enviornment) == correct_subject
