import os
import csv
import re
import collections
import logging
import optparse
import numpy
import codecs

import dedupe
from unidecode import unidecode
import itertools

import sys
import logging

#Setup

output_file = 'temp.csv'
settings_file = 'data_matching_learned_settings'
training_file = 'data_matching_training.json'

source_1 = 'master.csv'
source_2 = ''

master_heading = ['FIRST_NAME', 'LAST_NAME', 'PREFIX', 'SUFFIX', 'INDUSTRY', 'COMPANY', 'JOB_TITLE', 
                  'HOME_STREET', 'HOME_CITY', 'HOME_STATE', 'HOME_ZIPCODE', 'WORK_STREET', 
                  'WORK_CITY', 'WORK_STATE', 'WORK_ZIPCODE', 'HOME_PHONE', 'WORK_PHONE', 'EMAILS']


#Read in our data from a CSV file and create a dictionary of records, where the key is a unique record ID.

def readData(filename):
#
    data_d = {}

    with open(filename, 'rU') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            clean_row = dict([(k, v) for (k, v) in row.items()])
            data_d[filename + "##" + str(i)] = clean_row

    return data_d

def merge(records, headers, master_heading):
    try:
        # There should only be two or fewer records being merged
        assert records, headers
        assert len(records) <= 2
        assert len(headers) <= 2

        record_1 = records[0]

        record_2 = None
        if len(records) == 2:
            record_2 = records[1]

        merged_record = []

        for heading in master_heading:

            index_1 = headers[0].index(heading)
            field_1 = record_1[index_1]

            if len(headers) > 1 and record_2:
                index_2 = headers[1].index(heading)
                field_2 = record_2[index_2]

            if field_1 == "" and record_2 and field_2 != "":
                merged_record.append(field_2)
            else:
                merged_record.append(field_1)

        return merged_record

    except AssertionError:
        logging.warning("Records " + records + "were not merged.")
    except ValueError:
        logging.warning("A master heading was not matched to one of the merged files.")

def runProgram(new_source):

    source_2 = new_source  

    print 'importing data ...'
    data_1 = readData(source_1)
    data_2 = readData(source_2)

    #Training

    if os.path.exists(settings_file):
        print 'reading from', settings_file
        with open(settings_file) as sf :
            linker = dedupe.StaticRecordLink(sf)

    else:
    #Define the fields the linker will pay attention to

    #Notice how we are telling the linker to use a custom field comparator for the 'price' field.

        fields = [
            {'field' : 'FIRST_NAME', 'type': 'String'},
            {'field' : 'LAST_NAME', 'type': 'String'},
            {'field' : 'PREFIX', 'type': 'String', 'has missing' : True},
            {'field' : 'SUFFIX', 'type' : 'String', 'has missing' : True},
            {'field' : 'INDUSTRY', 'type' : 'String', 'has missing' : True},
            {'field' : 'COMPANY', 'type' : 'String', 'has missing' : True},
            {'field' : 'JOB_TITLE', 'type' : 'String', 'has missing' : True},
            {'field' : 'HOME_STREET', 'type' : 'String', 'has missing' : True},
            {'field' : 'HOME_CITY', 'type' : 'ShortString', 'has missing' : True},
            {'field' : 'HOME_STATE', 'type' : 'ShortString', 'has missing' : True},
            {'field' : 'HOME_ZIPCODE', 'type' : 'ShortString', 'has missing' : True},
            {'field' : 'WORK_STREET', 'type' : 'String', 'has missing' : True},
            {'field' : 'WORK_CITY', 'type' : 'ShortString', 'has missing' : True},
            {'field' : 'WORK_STATE', 'type' : 'ShortString', 'has missing' : True},
            {'field' : 'WORK_ZIPCODE', 'type' : 'ShortString', 'has missing' : True},
            {'field' : 'HOME_PHONE', 'type' : 'String', 'has missing' : True},
            {'field' : 'WORK_PHONE', 'type' : 'String', 'has missing' : True},
            {'field' : 'EMAILS', 'type' : 'Set', 'has missing' : True}]

    #Create a new linker object and pass our data model to it.

        linker = dedupe.RecordLink(fields)
    #To train the linker, we feed it a sample of records.

        linker.sample(data_1, data_2, 100)
    #If we have training data saved from a previous run of linker, look for it an load it in. Note: if you want to train from scratch, delete the training_file

        if os.path.exists(training_file):
            with open(training_file) as tf :
                linker.readTraining(tf)
    #Active learning

    #Dedupe will find the next pair of records it is least certain about and ask you to label them as matches or not. use 'y', 'n' and 'u' keys to flag duplicates press 'f' when you are finished

        dedupe.consoleLabel(linker)

        linker.train()
    #When finished, save our training away to disk

        with open(training_file, 'w') as tf :
            linker.writeTraining(tf)
    #Save our weights and predicates to disk. If the settings file exists, we will skip all the training and learning next time we run this file.

        with open(settings_file, 'w') as sf :
            linker.writeSettings(sf)

    #Clustering

    #Find the threshold that will maximize a weighted average of our precision and recall. When we set the recall weight to 2, we are saying we care twice as much about recall as we do precision.

    #If we had more data, we would not pass in all the blocked data into this function but a representative sample.

    linked_records = linker.match(data_1, data_2, 0)

    print '# duplicate sets', len(linked_records)
    #Writing Results

    #Write our original data back out to a merged CSV.
     
    cluster_membership = {}
    for cluster_id, (cluster, score) in enumerate(linked_records):
        cluster_membership[cluster_id] = []
        for record_id in cluster:
            split_on_csv = record_id.split("##", 1)
            file_name = split_on_csv[0]
            row = split_on_csv[1]
            cluster_membership[cluster_id].append((file_name, row))


    with open(output_file, 'w') as f:

        writer = csv.writer(f)
        writer.writerow(master_heading)

        clustered_rows = {}

        for cluster_id in cluster_membership:
            headers = []
            records = []
            for (file_name, row) in cluster_membership[cluster_id]:
                with open(file_name, "r") as f:
                    reader = csv.reader(f)
                    row = int(row)
                    header_row = next(itertools.islice(reader, 0, None))
                    selected_row = next(itertools.islice(reader, row, None))
                    records.append(selected_row)
                    headers.append(header_row)

                    if file_name in clustered_rows:
                        clustered_rows[file_name].append(row)
                    else:
                        clustered_rows[file_name] = [row]

            merged_record = merge(records, headers, master_heading)
            writer.writerow(merged_record)

        row_count_1 = sum(1 for row in csv.reader( open(source_1) ) )
        row_count_2 = sum(1 for row in csv.reader( open(source_2) ) )

        for num in range(row_count_1 - 1):
            if not source_1 in clustered_rows or num not in clustered_rows[source_1]:
                with open(source_1, "r") as f:
                    reader = csv.reader(f)
                    header_row = next(itertools.islice(reader, 0, None))
                    selected_row = next(itertools.islice(reader, num, None))
                    records = [selected_row]
                    headers = [header_row]

                    merged_record = merge(records, headers, master_heading)

                    writer.writerow(merged_record)

        for num in range(row_count_2 - 1):
            if not source_2 in clustered_rows or num not in clustered_rows[source_2]:
                with open(source_2, "r") as f:
                    reader = csv.reader(f)
                    header_row = next(itertools.islice(reader, 0, None))
                    selected_row = next(itertools.islice(reader, num, None))
                    records = [selected_row]
                    headers = [header_row]

                    merged_record = merge(records, headers, master_heading)

                    writer.writerow(merged_record)