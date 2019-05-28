import csv
import re
import requests
from bs4 import BeautifulSoup

DOCS = 'https://docs.newrelic.com'

def gen_integrations():
    """returns a tuple with an integration category, name and url"""
    response = requests.get(f'{DOCS}/docs/integrations?toc=true')
    soup = BeautifulSoup(response.text, 'html.parser')
    categories = soup.find_all('a', string=re.compile('.*Integrations List$'))
    for category in categories:
        integrations = category.find_next('ul').find_all('a')
        for integration in integrations:
            yield category.next, integration.next, f"{DOCS}{integration['href']}"


def gen_default_event_types(*filter_event_types):
    filter_event_types = [*filter_event_types]
    response = requests.get(f'{DOCS}/attribute-dictionary')
    soup = BeautifulSoup(response.text, 'html.parser')
    event_types = soup.find_all('input', attrs={'name': 'events_tids[]'})
    for event_type in event_types:
        event_name = event_type.find_next('label', class_='option').next
        if not filter_event_types or event_name in filter_event_types:
            event_tid = int(event_type['value'])
            yield event_name, event_tid


def gen_default_attributes(*filter_event_types):
    params = {}
    filter_event_types = [*filter_event_types]
    for event_name,event_tid in gen_default_event_types(*filter_event_types):
        print(event_name)
        params['events_tids[]'] = event_tid
        response = requests.get(f'{DOCS}/attribute-dictionary', params=params)
        soup = BeautifulSoup(response.text, 'html.parser')
        attributes = soup.find('div', string=f'{event_name} event').find_next()
        attributes = attributes.find_all('td', class_='views-field-title-1')
        for attribute in attributes:
            attribute = attribute.find('a')
            attr_name = attribute.next
            attr_descr = attribute.find_next('td').next.strip()
            yield {
                'eventType': event_name,
                'attribute': attr_name,
                'description': attr_descr
            }


with open('insights-default-attributes.csv', 'w') as csv_file:
    fieldnames = ['eventType', 'attribute', 'description']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for row in gen_default_attributes():
        writer.writerow(row)