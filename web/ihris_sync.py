#!/usr/bin/env python
import requests
import base64
import sys
import os
import psycopg2
import psycopg2.extras
import getopt
import logging
import pprint
from lxml import etree as ElementTree
from settings import config

logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(message)s', filename='/tmp/intrahealth.log',
    datefmt='%Y-%m-%d %I:%M:%S', level=logging.DEBUG
)
cmd = sys.argv[1:]
opts, args = getopt.getopt(
    cmd, 'd',
    ['debug'])

DEBUG = False
for option, parameter in opts:
    if option == '-d':
        DEBUG = True


def get_CSD_from_iHRIS(url=config['iHRIS_endpoint']):
    coded = base64.b64encode(
        "%s:%s" % (config['iHRIS_username'], config['iHRIS_password']))
    response = requests.get(
        url, headers={
            'Content-Type': 'text/xml',
            'Authorization': 'Basic ' + coded}
    )
    return response

parser = ElementTree.XMLParser(recover=True)

if DEBUG:
    filedir = os.path.dirname(os.path.abspath(__file__))
    print filedir
    with open('%s/test/ihris_resp.xml' % filedir)as f:
        tree = ElementTree.fromstring(f.read(), parser)
else:
    try:
        providers_stream = get_CSD_from_iHRIS()
        tree = ElementTree.fromstring(providers_stream.text, parser)
    except Exception as e:
        print str(e)
        sys.exit(1)

NS = {
    'csd': 'urn:ihe:iti:csd:2013',
    'soap': 'http://www.w3.org/2003/05/soap-envelope',
    'wsa': 'http://www.w3.org/2005/08/addressing'
}

PROVIDERS_LIST = []

providers = tree.xpath('//csd:provider', namespaces=NS)

print len(providers)
for p in providers:
    # try:
    entityID = p.xpath('./@entityID', namespaces=NS)[0]

    otherID = p.xpath('./csd:otherID', namespaces=NS)
    otherID = otherID[0].text if otherID else ''

    code = p.xpath('./csd:codedType/@code', namespaces=NS)
    code = code[0] if code else ''

    cadre = p.xpath('./csd:codedType', namespaces=NS)
    cadre = cadre[0].text if cadre else ''

    common_name = p.xpath('./csd:demographic/csd:name/csd:commonName[1]', namespaces=NS)
    common_name = common_name[0].text if common_name else ''

    firstname = p.xpath('./csd:demographic/csd:name/csd:forename', namespaces=NS)
    firstname = firstname[0].text if firstname else ''

    lastname = p.xpath('./csd:demographic/csd:name/csd:surname', namespaces=NS)
    lastname = lastname[0].text if lastname else ''

    othername = p.xpath('./csd:demographic/csd:name/csd:othername', namespaces=NS)
    othername = othername[0].text if othername else ''

    gender = p.xpath('./csd:demographic/csd:gender', namespaces=NS)
    gender = gender[0].text if gender else ''
    phones = []

    phone_contacts = p.xpath(
        './csd:demographic/csd:contactPoint/csd:codedType[@code="BP" and  '
        '@codingScheme="urn:ihe:iti:csd:2013:contactPoint"]', namespaces=NS)
    for phone in phone_contacts:
        phones.append(phone.text)
    emails = []
    email_contacts = p.xpath(
        './csd:demographic/csd:contactPoint/csd:codedType[@code="EMAIL" and  '
        '@codingScheme="urn:ihe:iti:csd:2013:contactPoint"]', namespaces=NS)
    for email in email_contacts:
        emails.append(email.text)

    cr1 = p.xpath('./csd:credential[1]', namespaces=NS)
    registration_number = ''
    registration_date = ''
    if cr1:
        registration_number = p.xpath('./csd:credential[1]/csd:number', namespaces=NS)
        registration_number = registration_number[0].text if registration_number else ''

        registration_date = p.xpath('./csd:credential[1]/csd:credentialIssueDate', namespaces=NS)
        registration_date = registration_date[0].text if registration_date else ''
    license_date = ''
    license_renewal = ''
    facility = ''
    facilities = p.xpath('./csd:facilities/csd:facility', namespaces=NS)
    if facilities:
        facility_urn = facilities[0].xpath('./@urn', namespaces=NS)
        facility_urn = facility_urn[0] if facility_urn else ''
        facility = facility_urn.split(':')[-1] if facility_urn.split(':') else ''

    cr2 = p.xpath('./csd:credential[2]/csd:number', namespaces=NS)
    if cr2:  # then licensed
        license_date = p.xpath('./csd:credential[2]/csd:credentialIssueDate', namespaces=NS)
        license_date = license_date[0].text if license_date else ''

        license_renewal = p.xpath('./csd:credential[2]/csd:credentialRenewalDate', namespaces=NS)
        license_renewal = license_renewal[0].text if license_renewal else ''

    provider = {
        'entityID': entityID, 'ihrisid': otherID, 'code': code, 'cadre': cadre,
        'firstname': firstname, 'lastname': lastname, 'commonname': common_name,
        'othername': othername, 'gender': gender, 'telephone': '', 'email': '',
        'registration_number': registration_number, 'registration_date': registration_date,
        'license_date': license_date, 'facility': facility, 'license_number': registration_number,
        'alt_tel': '', 'other_tel': '', 'alt_email': '', 'license_renewal': license_renewal
    }
    # cater for multiple phones and emails
    if len(phones) > 2:
        provider['alt_tel'] = phones[1]
        provider['other_tel'] = phones[2]
        provider['telephone'] = phones[0]
    elif len(phones) == 2:
        provider['alt_tel'] = phones[1]
        provider['telephone'] = phones[0]
    elif len(phones) == 1:
        provider['telephone'] = phones[0]

    if len(emails) > 1:
        provider['email'] = emails[1]
        provider['alt_email'] = emails[0]
    elif len(emails) == 1:
        provider['email'] = emails[0]

    PROVIDERS_LIST.append(provider)

    if DEBUG:
        print "OtherID: ", otherID
        print "EntityID: ", entityID
        print "Code: ", code
        print "Cadre: ", cadre
        print "Common Name: ", common_name
        print "First Name: ", firstname
        print "Last Name: ", lastname
        print "Other Name: ", othername
        print "Gender: ", gender
        print "Phones: ", phones
        print "Emails: ", emails
        print "Facility: ", "===>", facility
        print "Reg No.: ", registration_number
        print "Reg Date: ", registration_date
        print "License Date: ", license_date
        print "License Renewal: ", license_renewal
        print "============================"
    # except Exception as e:
    #     print p
    #     print str(e)
    #     continue
    #     # sys.exit(1)
if DEBUG:
    pprint.pprint(PROVIDERS_LIST[:4])

conn = psycopg2.connect(
    "dbname=" + config["db_name"] + " host= " + config["db_host"] + " port=" + config["db_port"] +
    " user=" + config["db_user"] + " password=" + config["db_passwd"])

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

ROLE_NAME_IDS = {}
# Preload HealthProvider Types
cur.execute("SELECT id, name FROM healthprovider_types")
res = cur.fetchall()
for r in res:
    ROLE_NAME_IDS[r['name']] = r['id']

# Add or Update HealthProvider
for provider in PROVIDERS_LIST:
    if provider['cadre'] in ROLE_NAME_IDS:
        provider['role'] = ROLE_NAME_IDS[provider['cadre']]
    else:
        cur.execute(
            "INSERT INTO healthprovider_types (name) "
            "VALUES (%s) RETURNING id, name", [provider['cadre']])
        res = cur.fetchone()
        if res:
            provider['role'] = res['id']
            ROLE_NAME_IDS[res['name']] = res['id']

    cur.execute("SELECT id FROM healthproviders WHERE ihrisid = %s", [provider['ihrisid']])
    res = cur.fetchone()
    if not res:  # no entry
        cur.execute(
            "INSERT INTO healthproviders (ihrisid, firstname, lastname, commonname, gender, "
            "telephone, alt_tel, other_tel, email, alt_email, facilityid, registration_number, "
            "registration_date, license_number, license_date, license_renewal, role) "
            "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "RETURNING id",
            [
                provider['ihrisid'], provider['firstname'], provider['lastname'],
                provider['commonname'], provider['gender'], provider['telephone'], provider['alt_tel'],
                provider['other_tel'], provider['email'], provider['alt_email'],
                provider['facility'], provider['registration_number'],
                provider['registration_date'] if provider['registration_date'] else None,
                provider['license_number'],
                provider['license_date'] if provider['license_date'] else None,
                provider['license_renewal'] if provider['license_renewal'] else None,
                provider['role']])
    else:  # update entry
        cur.execute(
            "UPDATE healthproviders SET (firstname, lastname, commonname, gender, telephone, "
            "alt_tel, other_tel, email, alt_email, facilityid, registration_number, "
            "registration_date, license_number, license_date, license_renewal, role) "
            " = (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "WHERE ihrisid = %s ",
            [
                provider['firstname'], provider['lastname'], provider['commonname'],
                provider['gender'], provider['telephone'], provider['alt_tel'],
                provider['other_tel'], provider['email'], provider['alt_email'],
                provider['facility'], provider['registration_number'],
                provider['registration_date'] if provider['registration_date'] else None,
                provider['license_number'],
                provider['license_date'] if provider['license_date'] else None,
                provider['license_renewal'] if provider['license_renewal'] else None,
                provider['role'], provider['ihrisid']])
    conn.commit()
conn.close()
