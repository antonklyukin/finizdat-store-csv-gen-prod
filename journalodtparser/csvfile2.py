#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C,R,locally-disabled

import csv
import journalparser2


journal_name = 're-11'

journal_info = journalparser2.gather_journal_info(f'./test_file/{journal_name}.odt')
flattened_journal_info = journalparser2.flatten_journal_info_dict(journal_info)


def csv_writer(data, path):
    """
    Write data to a CSV file path
    """
    with open(path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter='\t')
        for line in data:
            writer.writerow(line)


path = f'./test_file/{journal_name}.csv'
csv_writer(flattened_journal_info, path)
