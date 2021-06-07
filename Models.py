import datetime
import Models


class Issue:
    type = ''
    image = ''
    description = ''
    address = ''
    geo = ''
    send_time = None

    def __init__(self):
        self.send_time = datetime.datetime.now()


class User:
    id = 0
    state = 'init'
    last_action_time = datetime.datetime.now()
    issue = Issue()

    def reset_issue(self):
        self.issue = Issue()
