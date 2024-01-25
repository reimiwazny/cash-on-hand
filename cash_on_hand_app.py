import PySimpleGUI as sg
import cash_on_hand_api as db_api

config = {'Font': ('any', 15)}

quick_entry_keys_layout = [
                            [sg.Button('$1', size=[6,1], key='1'), sg.Button('$5', size=[6,1], key='5'), sg.Button('$10', size=[6,1], key='10')],
                            [sg.Button('$20', size=[6,1], key='20'), sg.Button('$50', size=[6,1], key='50'), sg.Button('$100', size=[6,1], key='100')],
                            [sg.Button('Add', size=[6,1], key='ADD'), sg.Multiline(size=(14,1), disabled=True, no_scrollbar=True, key='AMT')]
                          ]

recent_expenses_layout = [
                            [sg.Push(), sg.Text('Recent Expenses', size=(45,1), justification='center'), sg.Push()],
                            [sg.Push(), sg.Text('', size=(45,1), justification='center', key='RECENT1'), sg.Push()],
                            [sg.Push(), sg.Text('', size=(45,1), justification='center', key='RECENT2'), sg.Push()],
                            [sg.Push(), sg.Text('', size=(45,1), justification='center', key='RECENT3'), sg.Push()],
                            [sg.Push(), sg.Text('', size=(45,1), justification='center', key='RECENT4'), sg.Push()],
                            [sg.Push(), sg.Text('', size=(45,1), justification='center', key='RECENT5'), sg.Push()]
                        ]

main_window_layout = [[sg.Push(), sg.Text(f'${0.00:.2f}'), sg.Push()],
                     [sg.Frame(title='', layout=recent_expenses_layout, relief='flat')],
                     [sg.Push()],
                     [sg.Frame(title='',layout=quick_entry_keys_layout), sg.Push()]]

all_expenses_layout = [
                        [sg.Push(), sg.Text('PLACEHOLDER'), sg.Push()]
                      ]

expense_analysis_layout = [
                        [sg.Push(), sg.Text('PLACEHOLDER'), sg.Push()]
                          ]

export_import_layout = [
                        [sg.Push(), sg.Text('PLACEHOLDER'), sg.Push()]
                       ]

tabs_layout = [
                [sg.TabGroup([[sg.Tab(title='     Home    ', layout=main_window_layout),
                               sg.Tab(title='   Expenses  ',layout=all_expenses_layout),
                               sg.Tab(title='   Analysis  ', layout=expense_analysis_layout),
                               sg.Tab(title='Export/Import', layout=export_import_layout)]
                               ])]
              ]

window = sg.Window(title='CASH_APP_BETA',
                   layout=tabs_layout,
                   font=config['Font'])

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break

window.close()