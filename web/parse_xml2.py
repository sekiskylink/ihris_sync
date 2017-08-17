from lxml import etree as ElementTree
import sys
from xmljson import badgerfish as bf
from json import dumps, loads
# import pprint

parser = ElementTree.XMLParser(recover=True)
# with open('/Users/sam/Downloads/stream.xml')as f:
with open('/Users/sam/Downloads/ihris_resp.xml')as f:
    tree = ElementTree.fromstring(f.read(), parser)
print tree

# jobj = dumps(bf.data(tree))
# print jobj

NS = {
    'csd': 'urn:ihe:iti:csd:2013',
    'soap': 'http://www.w3.org/2003/05/soap-envelope',
    'wsa': 'http://www.w3.org/2005/08/addressing'
}
# providers = tree.xpath('/soap:Envelope/soap:Body/csd:getModificationsResponse/csd:CSD', namespaces=NS)
providers = tree.xpath('//csd:provider', namespaces=NS)
# providers = providers[0].xpath('//csd:provider', namespaces=NS)

print len(providers)
for p in providers[:100]:
    entityID = p.xpath('./@entityID', namespaces=NS)[0]
    code = p.xpath('./csd:codedType/@code', namespaces=NS)[0]
    cadre = p.xpath('./csd:codedType', namespaces=NS)[0].text
    common_name = p.xpath('./csd:demographic/csd:name/csd:commonName[1]', namespaces=NS)[0].text
    firstname = p.xpath('./csd:demographic/csd:name/csd:forename', namespaces=NS)[0].text
    lastname = p.xpath('./csd:demographic/csd:name/csd:surname', namespaces=NS)[0].text
    lastname = p.xpath('./csd:demographic/csd:name/csd:surname', namespaces=NS)[0].text
    othername = ''
    othername1 = p.xpath('./csd:demographic/csd:name/csd:othername', namespaces=NS)
    if othername1:
        othername = othername1[0].text
    gender = p.xpath('./csd:demographic/csd:gender', namespaces=NS)[0].text
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
    registration_number = p.xpath('./csd:credential[1]/csd:number', namespaces=NS)[0].text
    registration_date = p.xpath('./csd:credential[1]/csd:credentialIssueDate', namespaces=NS)[0].text
    license_date = ''
    license_renewal_date = ''
    facility = ''
    facilities = p.xpath('./csd:facilities/csd:facility', namespaces=NS)
    if facilities:
        facility_urn = facilities[0].xpath('./@urn', namespaces=NS)[0]
        facility = facility_urn.split(':')[-1] if facility_urn.split(':') else ''

    cr2 = p.xpath('./csd:credential[2]/csd:number', namespaces=NS)
    if cr2:  # then licensed
        license_date = p.xpath('./csd:credential[2]/csd:credentialIssueDate', namespaces=NS)[0].text
        license_renewal_date = p.xpath('./csd:credential[2]/csd:credentialRenewalDate', namespaces=NS)[0].text

    print entityID
    print code
    print cadre
    print common_name
    print firstname
    print lastname
    print othername
    print gender
    print phones
    print emails
    print "===>", facility
    print registration_number
    print registration_date
    print license_date
    print license_renewal_date
    print "============================"
    # print p.xpath('./csd:demographic/@code', namespaces={'csd': csd_xmlns})

# jobj = dumps(bf.data(tree))
# # print jobj
# ourjson = loads(jobj)
# providerDirectory = ourjson['%sCSD' % csd_xmlns]['%s%s' % (csd_xmlns, 'providerDirectory')]
# providers = (providerDirectory['%sprovider' % csd_xmlns])
# pprint.pprint(providers[0].keys())
