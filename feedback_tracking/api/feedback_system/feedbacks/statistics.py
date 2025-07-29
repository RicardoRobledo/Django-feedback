__author__ = 'Ricardo'
__version__ = '0.1'


def get_feedback_distribution(feedback_types, total_feedbacks):
    """
    Function to get feedback statistics

    :param feedback_types: list of feedback types
    :param total_feedbacks: total number of feedbacks
    :return: percentage of feedback types
    """

    return round(feedback_types / total_feedbacks * 100) if total_feedbacks > 0 else 0
