import datetime
import Models

class Issue:
    type = ''
    image = ''
    description = ''
    send_time = datetime.datetime.now()

class User:
    id = 0
    state = 'init'
    last_action_time = datetime.datetime.now()
    issue = Issue()



