import json
import web
from . import db
from app.tools.utils import format_msisdn


def get_webhook_msg(params, label='msg'):
    """Returns value of given lable from rapidpro webhook data"""
    values = json.loads(params['values'])  # only way we can get out Rapidpro values in webpy
    msg_list = [v.get('value') for v in values if v.get('label') == label]
    if msg_list:
        msg = msg_list[0].strip()
        if msg.startswith('.'):
            msg = msg[1:]
        return msg
    return ""


class iHRISRegistration:
    def POST(self):
        web.header("Content-Type", "application/json; charset=utf-8")
        params = web.input(input="name")
        msg = get_webhook_msg(params, 'msg')  # here we get rapidpro value with label msg
        msg = ' '.join([i for i in msg.split(' ') if i])

        ret = {
            "count": 0,
            "message": "No records found, or too many records!"
        }

        phone = format_msisdn(params.phone.replace(' ', ''))
        phone = phone.replace('+', '')

        SEARCH_SQL = (
            "SELECT name, commonname, registration_number, "
            "registration_date, license_number, license_date, license_renewal, "
            "gender, telephone, email, cadre FROM healthproviders_view ")

        hws = []
        if params.input == 'name':
            FINAL_SQL = SEARCH_SQL + (
                " WHERE cadre <> '' AND (name ilike $search OR commonname ilike $search)")
            hws = db.query(FINAL_SQL, {'search': '%%%s%%' % msg})
        elif params.input == 'number':

            FINAL_SQL = SEARCH_SQL + (
                " WHERE cadre <> '' AND (telephone ilike $search OR alt_tel ilike $search "
                "OR other_tel ilike $search) ")
            search_field = get_webhook_msg(params, 'msg2')
            hws = db.query(FINAL_SQL, {'search': '%%%s%%' % search_field})

        if hws:
            number_of_hws = len(hws)
            if number_of_hws > 3:
                ret['count'] = number_of_hws
                if params.input == 'number':
                    ret['message'] = "Too many records with number %s" % search_field
            elif number_of_hws == 1:
                healthworker = hws[0]
                name = healthworker['name']
                registration_number = healthworker['registration_number']
                # registration_date = healthworker['registration_date']
                license_number = healthworker['license_number']
                license_date = healthworker['license_date']
                # license_renewal = healthworker['license_renewal']
                cadre = healthworker['cadre']
                if registration_number:
                    message = '%s is registered as a %s' % (name, cadre)
                    if license_number:
                        message += (
                            " with an active license [No: %s" % license_number)
                        if license_date:
                            message += (", License Date: %s]" % (license_date))
                        else:
                            message += "]"
                    else:
                        message += " with no active license."
                else:
                    message = '%s is registered as a %s with No active license.' % (name, cadre)
                ret['count'] = 1
                ret['message'] = message

            else:
                message = "Results:\n"
                for h in hws:
                    message += "%s is registered as %s " % (h['name'], h['cadre'])
                    if h['registration_number']:
                        message += "[license No: %s" % h['registration_number']
                        if h['license_date']:
                            message += ", License Date: %s" % h['license_date']
                            if params.input == 'number':
                                message += ", Tel: %s]" % h['telephone']
                            else:
                                message += "]"
                        else:
                            message += "]"
                    else:
                        if h['license_number']:
                            message += "[license No %s" % h['license_number']
                            if h['license_date']:
                                message += ", License Date: %s" % h['license_date']
                                if params.input == 'number':
                                    message += ", Tel: %s]" % h['telephone']
                                else:
                                    message += "]"
                            else:
                                message += "]"
                        else:
                            message += "with No active license."
                    message += "\n"
                ret['count'] = number_of_hws
                ret['message'] = message
        else:
            # ret['message'] = '%s is NOT registered as a Health Worker!' % msg
            if params.input == 'name':
                ret['message'] = 'No Health Worker with name %s is registered!' % msg
            else:
                ret['message'] = 'No Health Worker with number %s is registered!' % msg

        return json.dumps(ret)
