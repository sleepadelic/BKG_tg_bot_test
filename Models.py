import datetime


class Issue:
    type = ''
    image = ''
    description = ''
    address = ''
    geo = ''
    send_time = None

    def __init__(self):
        self.send_time = datetime.datetime.now()


class Report_Conditions:
    report_date: str = None
    report_type: str = None


class User:
    id = 0
    state = 'init'
    last_action_time = datetime.datetime.now()
    issue = Issue()
    report_conditions = Report_Conditions()

    def reset_issue(self):
        self.issue = Issue()
        self.report_conditions = Report_Conditions()
