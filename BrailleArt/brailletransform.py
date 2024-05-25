# -*- coding: utf-8 -*-

import re
from .brailledata import *


braille_dic_invert = create_invert_dic()
braille_dic_90 = create_turn90_dic()
braille_dic_mirror = create_mirror_dic()


def invert(input_str, dot_for_blank=False):
    if dot_for_blank:
        braille_dic_invert['⣿'] = '⠄'
        braille_dic_invert['⠄'] = '⣿'
    else:
        braille_dic_invert['⣿'] = '⠀'
        braille_dic_invert['⠄'] = '⢿'

    result_str = ""
    for i in range(0, len(input_str), 1):
        try:
            result_str += braille_dic_invert[input_str[i]]
        except KeyError:
            result_str += input_str[i]

    return result_str



def mirror(input_str, line_delimiter='\n', dot_for_blank=False):
    line_arr = list(filter(None, re.split(" |\n", input_str)))
    results_arr = [''] * len(line_arr)
    for i in range(0, len(line_arr), 1):
        for j in range(len(line_arr[i])-1, -1, -1):
            try:
                results_arr[i] += braille_dic_mirror[line_arr[i][j]]
            except KeyError:
                results_arr[i] += line_arr[i][j]

    if dot_for_blank:
        return line_delimiter.join(results_arr).replace('⠀', '⠄')
    else:
        return line_delimiter.join(results_arr)



def turn_90(input_str, line_delimiter=' ', dot_for_blank=False):
    line_arr = list(filter(None, re.split(" |\n", input_str)))
    longest_line = len(max(line_arr, key=len))
    new_line_arr = [' '] * (int(longest_line/2) + longest_line % 2)

    for line in line_arr:
        line_chunks = [line[i:i + 2] for i in range(0, len(line), 2)]
        for j in range(0, len(line_chunks), 1):
            try:
                new_chunk = braille_dic_90[line_chunks[j]]
            except KeyError:
                if j == len(line_chunks)-1 and len(line_chunks[j]) == 1:
                    new_chunk = ''
                else:
                    new_chunk = line_chunks[j]
            new_line_arr[j] = new_chunk + new_line_arr[j]

    if dot_for_blank:
        return line_delimiter.join(new_line_arr).replace('⠀', '⠄')
    else:
        return line_delimiter.join(new_line_arr)


def turn_180(input_str, line_delimiter=' ', dot_for_blank=False):
    return turn_90(turn_90(input_str, line_delimiter, dot_for_blank), line_delimiter, dot_for_blank)


def turn_270(input_str, line_delimiter=' ', dot_for_blank=False):
    return turn_90(turn_180(input_str,line_delimiter, dot_for_blank), line_delimiter, dot_for_blank)
