#!/usr/bin/env python
from datetime import date, timedelta
import time
import xmltodict
import requests

from scrapi_tools.consumers import BaseConsumer, RawFile, NormalizedFile


class ClinicalTrialsConsumer(BaseConsumer):

    def __init__(self):
        # what do?
        pass

    def consume(self):
        results = []

        """ First, get a list of all recently updated study urls,
        then get the xml one by one and save it into a list 
        of docs including other information """

        today = date.today()
        yesterday = today - timedelta(1)

        month = today.strftime('%m')
        day = today.strftime('%d')
        year = today.strftime('%Y')

        y_month = yesterday.strftime('%m')
        y_day = yesterday.strftime('%d')
        y_year = yesterday.strftime('%Y')

        base_url = 'http://clinicaltrials.gov/ct2/results?lup_s=' 
        url_end = '{}%2F{}%2F{}%2F&lup_e={}%2F{}%2F{}&displayxml=true'.\
                    format(y_month, y_day, y_year, month, day, year)

        url = base_url + url_end

        # grab the total number of studies
        initial_request = requests.get(url)
        initial_request = xmltodict.parse(initial_request.text)
        count = initial_request['search_results']['@count']

        results = []

        try:
            # get a new url with all results in it
            url = url + '&count=' + count
            total_requests = requests.get(url)
            response = xmltodict.parse(total_requests.text)

            # make a list of urls from that full list of studies
            study_urls = []
            for study in response['search_results']['clinical_study']:
                study_urls.append(study['url'] + '?displayxml=true')

            # grab each of those urls for full content
            for study_url in study_urls:
                content = requests.get(study_url)
                results.append(content.text)
                time.sleep(1)

        except KeyError: 
            print "No new files/updates!"

        return [RawFile(result) for result in results]


    def normalize(self, raw_doc, timestamp):
        result = xmltodict.parse(raw_doc)

        doc_attributes = {
            "doc": {
                'title': result['clinical_study']['brief_title'],
                'contributors': result['clinical_study']['overall_official']['last_name'],
                'properties': {
                    'abstract': result['clinical_study']['brief_summary']['textblock']
                },
                'meta': {},
                'id': result['clinical_study']['id_info']['nct_id'],
                'source': "ClinicalTrials.gov",
                'timestamp': str(timestamp)
            }
        }

        return NormalizedFile(doc_attributes)


ct_object = ClinicalTrialsConsumer()
ct_object.lint()

