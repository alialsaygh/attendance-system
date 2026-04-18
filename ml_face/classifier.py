# simple rule based classifier for student attendance behaviour
# we kept it simple because we only have 5 students and limited sessions

def classify_student(percentage, late_percentage, total_sessions):
    # need at least 3 sessions before we can say anything meaningful
    if total_sessions < 3:
        return 'Insufficient data'

    if percentage is None:
        return 'No sessions yet'

    # apply thresholds
    if percentage >= 80 and late_percentage < 20:
        return 'On Time'
    elif percentage >= 70 and late_percentage >= 20:
        return 'Frequently Late'
    elif percentage >= 50:
        return 'Irregular'
    else:
        return 'At Risk'


def get_badge_colour(classification):
    # returns bootstrap badge colour for each classification
    colours = {
        'On Time':           'success',
        'Frequently Late':   'warning',
        'Irregular':         'orange',    # we use custom style for this
        'At Risk':           'danger',
        'Insufficient data': 'secondary',
        'No sessions yet':   'secondary',
    }
    return colours.get(classification, 'secondary')