#!/bin/env python

import os
import random
import json
import unicodedata

COUNTRIES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              'countries.json')
MAX_N_OPTS = 8
DELIM = ','
NONE = '-'

NEG_PREFIXES = 'mμnpfazyrq'
POS_PREFIXES = 'kMGTPEZYRQ'
INFO_MSG = f'''
Info:
* Empty input ends the script.
* If options are given, the indices of options are accepted as answers.
* Multiple answers to a question separated by '{DELIM}' are possible.
* Single-choice questions are denoted with parentheses.
* Multiple-choice questions are denoted with brackets.
* Country data source: `https://github.com/mledoze/countries`.
* Areas are rounded to two significant digits.
'''
inf = float('inf')

with open(COUNTRIES_PATH, 'r') as file:
    countries = json.load(file)


class InputException(Exception):
    pass


def exponent(n):
    n = abs(n)
    if n == inf:
        return inf
    elif n == 0:
        return -inf
    e = 0
    while n < 10**e:
        e -= 1
    while n >= 10**(e+1):
        e += 1
    return e


def normalize(string):
    return ''.join(char
                   for char in unicodedata.normalize('NFD', string)
                   if unicodedata.category(char) != 'Mn')


def capitalize(string):
    return string[:1].upper() + string[1:]


def red(string):
    return f'\x1b[1;31m{string}\x1b[m'


def green(string):
    return f'\x1b[1;32m{string}\x1b[m'


def errmsg(string):
    print('Error: ' + string + '.')


def arr2str(arr):
    return (DELIM + ' ').join(sorted(arr))


def short_float(num):
    string = str(num)
    num = float(num)
    e = exponent(num)
    if abs(e) == inf:
        return string
    i = e//3
    r = e%3
    num = round(num*10**-(3*i), 1 - r)
    num = f'{int(num)}' if r > 0 else f'{num:.1f}'
    prefix = ''
    if i != 0:
        prefixes = POS_PREFIXES if i > 0 else NEG_PREFIXES
        i = abs(i) - 1
        if i < len(prefixes):
            prefix = prefixes[i]
        else:
            num = string
    return num + prefix


def adjust_float(num):
    string = num
    last_char = num[-1]
    if last_char in NEG_PREFIXES:
        num = num[:-1] + f'e-{3*(NEG_PREFIXES.index(last_char)+1)}'
    elif last_char in POS_PREFIXES:
        num = num[:-1] + f'e+{3*(POS_PREFIXES.index(last_char)+1)}'
    try:
        num = short_float(num)
    except:
        num = string
    return num


def adjust_str(string):
    string = normalize(string).lower()
    while '  ' in string:
        string = string.replace('  ', ' ')
    return string


def read_input(arr=False, multiple=False):
    tokens = input()
    tokens = tokens.strip()
    if not tokens:
        raise InputException()
    if arr:
        tokens = ([token.strip() for token in tokens.split(DELIM)]
                  if multiple
                  else [tokens])
    return tokens


def choose(head, multiple=False):
    print(f'\n{capitalize(head)}:')
    choice = read_input(True, multiple)
    return arr2str(choice)


def choose_int(head, lower, upper, other=[]):
    choices = f'{lower}..{upper}'
    if other:
        choices += f' or {arr2str(str(elem) for elem in other)}'
    print(f'\n{capitalize(head)} ({choices}):')
    repeat = True
    while repeat:
        repeat = False
        choice = read_input()
        try:
            choice = int(choice)
        except:
            errmsg('Only an integer is accepted')
            repeat = True
        if not (lower <= choice <= upper or choice in other):
            errmsg(f'The integer should be one of {choices}')
            repeat = True
    return choice


def choose_opts(head, choices, multiple=False):
    brackets = '[]' if multiple else '()'
    body = '\n'.join(f'{brackets[0]}{i+1}{brackets[1]} {choice}'
                     for i, choice in enumerate(choices))
    print(f'\n{capitalize(head)}:\n{body}')
    repeat = True
    while repeat:
        repeat = False
        tokens = read_input(True, multiple)
        choice = set()
        for token in tokens:
            if token.isdigit():
                idx = int(token) - 1
                if not 0 <= idx < len(choices):
                    errmsg(f'{token} is not a valid option index')
                    repeat = True
                    break
                choice.add(choices[idx])
            else:
                errmsg('Only one option index is accepted'
                       if DELIM in token and not multiple
                       else 'Only option indices are accepted')
                repeat = True
                break
    return arr2str(choice)


def main():
    try:
        print(INFO_MSG)
        
        topics = [
            'capital',
            'flag',
            'languages',
            'two-letter code',
            'three-letter code',
            'region',
            'subregion',
            'borders',
            'area',
        ]
        limits = [
            'independence',
            'location',
            'size',
            'island or not',
        ]
        
        topic = choose_opts('topic', topics)
        direction = choose_opts('direction', [f'country -> {topic}',
                                              f'country <- {topic}'])
        ask_topic = ' -> ' in direction
        name = choose_opts('country names', ['common', 'official'])
        limit = choose_opts('limit questions', ['no', 'yes'])
        conditions = []
        if limit == 'yes':
            condition_list = choose_opts('limiting conditions', limits, True)
            if 'independence' in condition_list:
                choice = choose_opts('independent', ['yes', 'no'])
                condition = ((lambda country: country['independent'])
                             if choice == 'yes' else
                             (lambda country: not country['independent']))
                conditions.append(condition)
            if 'location' in condition_list:
                location = choose_opts('location', ['region', 'subregion'])
                options = sorted(set(country[location]
                                     for country in countries
                                     if country[location]))
                locations = choose_opts(location, options, True)
                locations = locations.split(DELIM + ' ')
                condition = lambda country: country[location] in locations
                conditions.append(condition)
            if 'size' in condition_list:
                size = choose_opts('size', ['big (> 10k km²)',
                                            'large (> 1M km²)',
                                            'small (< 10k km²)'])
                if size.startswith('big'):
                    condition = lambda country: country['area'] >= 1e4
                elif size.startswith('large'):
                    condition = lambda country: country['area'] >= 1e6
                elif size.startswith('small'):
                    condition = lambda country: country['area'] < 1e4
                conditions.append(condition)
            if 'island or not' in condition_list:
                island = choose_opts('island', ['no', 'yes'])
                condition = ((lambda country: bool(country['borders']))
                             if choice == 'yes' else
                             (lambda country: not bool(country['borders'])))
                conditions.append(condition)
        condition = lambda country: all(cond(country) for cond in conditions)
        
        key = topic
        check = lambda data: bool(data)
        convert = lambda data: data
        single_token = True
        conjunction = 'with'
        adjust = lambda data: adjust_str(data)
        if topic == 'capital':
            convert = lambda data: arr2str(data)
            single_token = False
        elif topic == 'languages':
            check = lambda data: len(data) > 0
            convert = lambda data: arr2str(data.values())
            single_token = False
            conjunction = 'speaking'
        elif topic == 'two-letter code':
            key = 'cca2'
            conjunction = 'abbreviated as'
        elif topic == 'three-letter code':
            key = 'cca3'
            conjunction = 'abbreviated as'
        elif topic == 'region':
            conjunction = 'in'
        elif topic == 'subregion':
            conjunction = 'in'
        elif topic == 'borders':
            code2country = {country['cca3']: country['name']['common']
                            for country in countries}
            check = lambda data: True
            convert = lambda data: arr2str(code2country[code] for code in data)
            single_token = False
            conjunction = 'bordering'
        elif topic == 'area':
            topic = 'area (in km²)'
            check = lambda data: float(data) >= 0
            convert = lambda data: short_float(data)
            adjust = lambda data: adjust_float(data)
        
        questions = []
        answers = []
        arr1, arr2 = ((questions, answers) if ask_topic
                      else (answers, questions))
        for country in countries:
            if condition(country):
                data = country[key]
                if check(data):
                    arr1.append(country['name'][name])
                    data = convert(data)
                    arr2.append(data if data else NONE)
        answer_set = set(answers)
        n_answers = len(answer_set)
        if n_answers < 2:
            errmsg('Not enough possible answer options')
            raise InputException()
        n_opts = choose_int('number of options', 2, min(MAX_N_OPTS, n_answers),
                            [0] if len(set(questions)) == len(questions)
                            else [])
        if n_opts > 0:
            no_opts = False
            var_opts = True
            multiple_answers = not ask_topic
            if n_opts == n_answers:
                var_opts = False
                options = sorted(answer_set)
                multiple_answers = False
            adjust = lambda data: data
        else:
            no_opts = True
            multiple_tokens = ask_topic and not single_token
            multiple_answers = False
        
        questionnaire = [(question, answer)
                         for question, answer in zip(questions, answers)]
        n_mistakes = 0
        tot_n_questions = len(questionnaire)
        print(f'\nInfo: There are {tot_n_questions} questions. Good luck!')
        while len(questionnaire) > 0:
            question, answer = random.choice(questionnaire)
            answer = {answer}
            head = ((f'{topic} of' if ask_topic else f'country {conjunction}')
                    + f' {question}')
            if no_opts:
                choice = choose(head, multiple_tokens)
            else:
                if var_opts:
                    options = {*answer}
                    while len(options) < n_opts:
                        choice = random.randint(0, len(answers) - 1)
                        option = answers[choice]
                        if option not in options:
                            if question != questions[choice]:
                                options.add(option)
                            elif multiple_answers:
                                answer.add(option)
                                options.add(option)
                    options = sorted(options)
                choice = choose_opts(head, options, multiple_answers)
            if adjust(choice) == adjust(arr2str(answer)):
                for answer in sorted(answer):
                    questionnaire.remove((question, answer))
                n_questions = tot_n_questions - len(questionnaire)
                print(green('Right!')
                      + f' Progress: {n_questions} out of {tot_n_questions}'
                      + ' questions answered correctly.')
            else:
                n_mistakes += 1
                print(red('Wrong!')
                      + f' The right answer is {arr2str(answer)}.')
        
        text = f'made {red(n_mistakes)} mistakes'
        if n_mistakes == 0:
            text = 'did not make any mistakes'
        elif n_mistakes == 1:
            text = text[:-1]
        print('\n' + green('Congratulations on completing the questionnaire!')
              + f' You {text}.')
        
    except InputException:
        return


if __name__ == '__main__':
    main()
