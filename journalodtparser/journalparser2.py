#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import re
import sys
from odtfile import OdtFile
from unidecode import unidecode


def correct_tree(odt_content, style_name, tag_name):

    nodes_list = odt_content.find_all('style:style',
                                      {'style:parent-style-name': style_name})
    list_of_node_number_styles = []

    for node in nodes_list:
        if node['style:name'] not in list_of_node_number_styles:
            list_of_node_number_styles.append(node['style:name'])

    for number_style in list_of_node_number_styles:
        nodes_list = odt_content.find_all(tag_name,
                                          {'text:style-name': number_style})
        for node in nodes_list:
            element = odt_content.find(
                tag_name, {'text:style-name': number_style})
            element['text:style-name'] = style_name


def has_cyrillic(text):

    return bool(re.search('[\u0400-\u04FF]', text))


def clear_text(text):

    stripped_text = text.strip()
    undoublespaced_text = re.sub(r'\s+', ' ', stripped_text)

    return undoublespaced_text


def get_journal_title(odt_content, journal_info):

    journal_title_with_tags = odt_content.find_all('svg:title')

    try:
        if not journal_title_with_tags:
            raise ValueError('Отсутствует название журнала в титульном '
                             'листе макета.')
        else:
            if has_cyrillic(journal_title_with_tags[0].get_text()):
                journal_title = ({'JOURNAL_NAME_RU':
                                  journal_title_with_tags[0].get_text()})
            else:
                raise ValueError('Отстутствует название журнала '
                                 'на русском языке в титульном листе макета.')
    except ValueError as error:
        print(str(error) + ' Программа остановлена.')
        sys.exit(1)
    else:
        if 'JOURNAL' not in journal_info:
            journal_info['JOURNAL'] = {}
        journal_info['JOURNAL'] = journal_title


def get_number_of_articles_in_journal(odt_content, journal_info):

    if 'ARTICLES' not in journal_info:
        journal_info['ARTICLES'] = {}

    number_of_articles = 0
    for element in odt_content.find_all('text:p'):
        if 'Для цитирования' in element.get_text():
            number_of_articles += 1

    if 'JOURNAL' not in journal_info:
        journal_info['JOURNAL'] = {}
    journal_info['JOURNAL']['NUMBER_OF_ARTICLES'] = number_of_articles


def get_month_name_of_issue(journal_info):

    issue_number = journal_info['JOURNAL']['ISSUE_NUMBER']
    journal_name = journal_info['JOURNAL']['JOURNAL_NAME_RU']

    quarterly_journals = ['Финансовая аналитика: проблемы и решения']

    month_names_dict = {}

    if (journal_name not in quarterly_journals):
        month_names_dict = {1: 'январь',
                            2: 'февраль',
                            3: 'март',
                            4: 'апрель',
                            5: 'май',
                            6: 'июнь',
                            7: 'июль',
                            8: 'август',
                            9: 'сентябрь',
                            10: 'октябрь',
                            11: 'ноябрь',
                            12: 'декабрь'}
    else:
        month_names_dict = {1: 'февраль',
                            2: 'май',
                            3: 'август',
                            4: 'ноябрь'}

    month_name = month_names_dict[int(issue_number)]

    return(month_name)


def get_info_from_citation_paragraph(odt_content, journal_info):

    i = 1

    regex_ru_citation = re.compile(r'^Для цитирования:\s(.*?[А-ЯЁ]\.)[\s]+(.*)'
                                   r'[\s]+//[\s]+?.*([2][0][1-9][0-9]).*Т\.'
                                   r'[\s]+?([\d][\d]),[\s]+?№\s?(\d\d?)\..*'
                                   r'С\.?[\s]+?([\d\s–-]+)')
    publication_year = 0
    journal_volume = 0
    issue_number = 0

    for element in odt_content.find_all('text:p'):
        if 'Для цитирования' in element.get_text():

            result = regex_ru_citation.match(clear_text(element.get_text()))

            authors_ru = result.group(1)
            article_name_ru = result.group(2)
            year = result.group(3)
            volume = result.group(4)
            number = result.group(5)
            pages_range = result.group(6)

            journal_info['ARTICLES'][i] = {}

            (journal_info['ARTICLES'][i]
             ['ARTICLE_NAME_SENTENCE_CASE_RU']) = clear_text(article_name_ru)

            journal_info['ARTICLES'][i]['AUTHORS_RU'] = clear_text(authors_ru)

            if publication_year == 0:
                publication_year = year

            if journal_volume == 0:
                journal_volume = volume

            if issue_number == 0:
                issue_number = number

            journal_info['ARTICLES'][i]['PAGES'] = pages_range

            i += 1

        if 'JOURNAL' not in journal_info:
            journal_info['JOURNAL'] = {}

        journal_info['JOURNAL']['PUBLICATION_YEAR'] = publication_year
        journal_info['JOURNAL']['JOURNAL_VOLUME'] = journal_volume
        journal_info['JOURNAL']['ISSUE_NUMBER'] = issue_number


def get_article_abstract_html(odt_content, journal_info):

    p_tags = odt_content.find_all('text:p')
    abstracts_list = []  # List of all abstract of issue
    for p_tag in p_tags:
        if 'Аннотация' in p_tag.get_text():
            abstract = ''  # Final string for joined paragraphs
            abstract_paragraphs = []  # List of all paragraphs of abstract
            for sibling in p_tag.next_siblings:  # Collect all paragraphs to
                # list (All paragraphs of same level in table)
                paragraph_text = sibling.get_text()

                if ('Издательский дом ФИНАНСЫ и КРЕДИТ' not in
                        paragraph_text and paragraph_text != ''):
                    # Why 'and', not 'or' but it works!?
                    abstract_paragraphs.append('<p>')  # Add HTML tags
                    abstract_paragraphs.append(clear_text(paragraph_text))
                    abstract_paragraphs.append('</p>\n')

            abstracts_list.append(abstract.join(abstract_paragraphs))

    for i, item in enumerate(abstracts_list, 1):  # Populate journal_info
        # dictionary with found abstracts
        journal_info['ARTICLES'][i]['ABSTRACT_HTML_RU'] = item


def get_article_rubric(odt_content, journal_info):

    style_name_ru = 'СтатьяРубрикаРус'

    correct_tree(odt_content, style_name_ru, 'text:p')

    rubric_names_ru_list = odt_content.find_all(
        'text:p', {'text:style-name': style_name_ru})

    # Creating key ARTICLES in global dictionary of journal information if
    # not exist
    if 'ARTICLES' not in journal_info:
        journal_info['ARTICLES'] = {}

    i = 1
    for rubric in rubric_names_ru_list:
        if rubric.get_text() == '':
            continue 
        if i not in journal_info['ARTICLES']:
            journal_info['ARTICLES'][i] = {}
        journal_info['ARTICLES'][i]['RUBRIC_NAME_RU'] = rubric.get_text()
        i += 1


def get_article_keywords(odt_content, journal_info):  # Очень медленная функция,
    # переписать

    style_name_ru = 'СтатьяИнфоРус'

    correct_tree(odt_content, style_name_ru, 'text:p')

    info_ru_list = odt_content.find_all(
        'text:p', {'text:style-name': style_name_ru})

    keywords_ru_list = []

    for element in info_ru_list:
        if 'Ключевые слова:' in (element.get_text()):
            element_string = element.get_text()
            cleared_string = element_string.replace('Ключевые слова: ', '')
            keywords_ru_list.append(cleared_string)

    # Creating key ARTICLES in global dictionary of journal information if
    # not exist
    if 'ARTICLES' not in journal_info:
        journal_info['ARTICLES'] = {}

    for i, item in enumerate(keywords_ru_list, 1):
        if i not in journal_info['ARTICLES']:
            journal_info['ARTICLES'][i] = {}
        journal_info['ARTICLES'][i]['KEYWORDS_RU'] = clear_text(item)


def get_journal_id(journal_name_ru):

    journal_ids_dict = {'Финансы и кредит': 'fc',
                        'Экономический анализ: теория и практика': 'ea',
                        'Региональная экономика: теория и практика': 're',
                        'Национальные интересы: приоритеты и '
                        'безопасность': 'ni',
                        'Финансовая аналитика: проблемы и решения': 'fa',
                        'Международный бухгалтерский учет': 'ia'}
    return(journal_ids_dict[journal_name_ru])


def get_article_good_id(journal_info, article_number):

    journal_id = get_journal_id(journal_info['JOURNAL']['JOURNAL_NAME_RU'])
    issue_number = journal_info['JOURNAL']['ISSUE_NUMBER']
    page_range = journal_info['ARTICLES'][article_number]['PAGES']
    publication_year = journal_info['JOURNAL']['PUBLICATION_YEAR']

    pages_list = page_range.split()
    first_page = pages_list[0]

    delimiter = '-'
    return(delimiter.join([journal_id.upper(), issue_number.zfill(2),
                           publication_year, first_page]))


def create_journal_abstract_text(journal_info):

    abstract = '<h2>СОДЕРЖАНИЕ</h2>'
    prev_rubric_name = 0
    for i in range(len(journal_info['ARTICLES'])):
        i += 1
        article_name = (journal_info['ARTICLES'][i]
                        ['ARTICLE_NAME_SENTENCE_CASE_RU'])
        rubric_name = (journal_info['ARTICLES'][i]
                       ['RUBRIC_NAME_RU'])

        author_names = (journal_info['ARTICLES'][i]
                        ['AUTHORS_RU'])
        if (rubric_name != prev_rubric_name) or (prev_rubric_name == 0):
            abstract += '<p><strong>{0}</strong></p>\n'.format(
                rubric_name.upper())
        abstract += '<p><em>{0}</em> {1}</p>\n'.format(
            author_names, article_name)

        prev_rubric_name = rubric_name

    return abstract


def create_abstract_text(journal_name, issue_year, issue_volume, issue_number,
                         article_pages, article_authors, article_rubric,
                         article_abstract, article_keywords):
    abstract = ''
    abstract += '<p><strong>Статья опубликована в журнале: </strong> {0}, \
{1}, Т.&nbsp;{2}, №&nbsp;{3}, С.&nbsp;{4}</p>\n'.format(journal_name, issue_year,
                                         issue_volume, issue_number,
                                         article_pages)
    abstract += '<p><strong>Автор(ы):</strong> {0}</p>\n'.format(
        article_authors)
    abstract += '<p><strong>Рубрика:</strong> {0}</p>\n'.format(article_rubric)
    abstract += '<p><strong>Аннотация</strong></p>\n'
    abstract += '{0}'.format(article_abstract)
    abstract += '<p><strong>Ключевые слова:</strong> {0}\n'.format(
        article_keywords)

    return abstract


def flatten_journal_info_dict(journal_info):

    journal_info_flatted = []

    journal_info_flatted.append(['Название товара',
                                 'Название товара в URL',
                                 'Полное описание',
                                 'Видимость на витрине',
                                 'Применять скидки',
                                 'Размещение на сайте',
                                 'Валюта склада',
                                 'НДС',
                                 'Единица измерения',
                                 'Артикул',
                                 'Цена продажи',
                                 'Параметр: Категория Яндекс Маркета',
                                 'Параметр: Тип публикации',
                                 'Параметр: Формат',
                                 'Параметр: Журнал',
                                 'Параметр: Год публикации',
                                 'Параметр: Месяц публикации'])

    for i in range(len(journal_info['ARTICLES'])):
        j = i + 1
        article = []

        issue_month_name = get_month_name_of_issue(journal_info)
        site_structure_location = (journal_info['JOURNAL']['JOURNAL_NAME_RU'])
        publication_type = 'Статья'
        file_type = 'PDF'
        unit_of_measurement = 'шт'
        # journal_id = get_journal_id(journal_info['JOURNAL']
        # ['JOURNAL_NAME_RU'])
        article_good_id = get_article_good_id(journal_info, j)

        abstract_text = create_abstract_text(
            journal_info['JOURNAL']['JOURNAL_NAME_RU'],
            journal_info['JOURNAL']['PUBLICATION_YEAR'],
            journal_info['JOURNAL']['JOURNAL_VOLUME'],
            journal_info['JOURNAL']['ISSUE_NUMBER'],
            journal_info['ARTICLES'][j]['PAGES'],
            journal_info['ARTICLES'][j]['AUTHORS_RU'],
            journal_info['ARTICLES'][j]['RUBRIC_NAME_RU'],
            journal_info['ARTICLES'][j]['ABSTRACT_HTML_RU'],
            journal_info['ARTICLES'][j]['KEYWORDS_RU'])

        translated_article_name = unidecode(journal_info['ARTICLES'][j]
                                            ['ARTICLE_NAME_SENTENCE_CASE_RU'].
                                            lower().replace(' ', '-'))

        translated_article_name = re.sub(r'[\'\:\"\)\(\\\№]', '',
                                         translated_article_name)

        article_price = '150,0'
        visibility = 'выставлен'
        enable_discount = 'да'
        currency = 'RUR'
        vat = 'Без НДС'
        yandex_market_name = 'Все товары/Досуг и развлечения/Книги/\
Журналы и газеты/Наука и образование'

        article.append(journal_info['ARTICLES'][j]
                       ['ARTICLE_NAME_SENTENCE_CASE_RU'])
        article.append(translated_article_name)
        article.append(abstract_text)
        article.append(visibility)
        article.append(enable_discount)
        article.append(site_structure_location)
        article.append(currency)
        article.append(vat)
        article.append(unit_of_measurement)
        article.append(article_good_id)
        article.append(article_price)
        article.append(yandex_market_name)
        article.append(publication_type)
        article.append(file_type)
        article.append(journal_info['JOURNAL']['JOURNAL_NAME_RU'])
        article.append(journal_info['JOURNAL']['PUBLICATION_YEAR'])
        article.append(issue_month_name)

        journal_info_flatted.append(article)

    # Creating journal item at last

    publication_year = journal_info['JOURNAL']['PUBLICATION_YEAR']

    article = []

    issue_month_name = get_month_name_of_issue(journal_info)
    site_structure_location = (journal_info['JOURNAL']['JOURNAL_NAME_RU'])
    publication_type = 'Номер журнала'
    file_type = 'PDF'
    unit_of_measurement = 'шт'
    article_good_id = '###'
    abstract_text = create_journal_abstract_text(journal_info)
    translated_article_name = 'journal_issue'
    article_price = '3000,0'
    visibility = 'выставлен'
    enable_discount = 'да'
    currency = 'RUR'
    vat = 'Без НДС'
    yandex_market_name = 'Все товары/Досуг и развлечения/Книги/\
Журналы и газеты/Наука и образование'

    journal_name_ru = journal_info['JOURNAL']['JOURNAL_NAME_RU']

    article.append('«{0}», {1} {2}'.format(
        journal_name_ru, issue_month_name, publication_year))
    article.append(translated_article_name)
    article.append(abstract_text)
    article.append(visibility)
    article.append(enable_discount)
    article.append(site_structure_location)
    article.append(currency)
    article.append(vat)
    article.append(unit_of_measurement)
    article.append(article_good_id)
    article.append(article_price)
    article.append(yandex_market_name)
    article.append(publication_type)
    article.append(file_type)
    article.append(journal_name_ru)
    article.append(publication_year)
    article.append(issue_month_name)

    journal_info_flatted.append(article)

    return(journal_info_flatted)


def gather_journal_info(file_name):

    file = OdtFile(file_name)

    odt_content = BeautifulSoup(file.get_content_file_unicode(), 'lxml-xml')

    journal_info = {}  # Global dictionary of journal data

    get_journal_title(odt_content, journal_info)
    get_number_of_articles_in_journal(odt_content, journal_info)
    get_info_from_citation_paragraph(odt_content, journal_info)
    get_month_name_of_issue(journal_info)
    get_article_abstract_html(odt_content, journal_info)
    get_article_rubric(odt_content, journal_info)
    get_article_keywords(odt_content, journal_info)

    return(journal_info)


# journal_info = gather_journal_info('./test_file/EA-2018-12.odt')

# print(journal_info)


# flattened_journal_info = flatten_journal_info_dict(journal_info)
