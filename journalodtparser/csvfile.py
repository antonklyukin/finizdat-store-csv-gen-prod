#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C,R,locally-disabled

import csv
import journalparser


journal_info = journalparser.process_journal_info('./test_file/ea.odt')
flattened_journal_info = journalparser.flatten_journal_info_dict(journal_info)


def csv_writer(data, path):
    """
    Write data to a CSV file path
    """
    with open(path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter='\t')
        for line in data:
            writer.writerow(line)


path = './test_file/ea.csv'
csv_writer(flattened_journal_info, path)
