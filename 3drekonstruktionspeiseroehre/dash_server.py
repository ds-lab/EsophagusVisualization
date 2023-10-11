import socket

import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
import waitress
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import (DashProxy, Input, MultiplexerTransform,
                                    Output, State, dcc, html, no_update)
from kthread import KThread
from PyQt5.QtWidgets import QMessageBox

import config
from logic.visit_data import VisitData


class DashServer:
    """Represents the dash server that is needed for the visualization"""

    button_text_start = 'Animation starten'
    button_text_stop = 'Animation anhalten'

    def __init__(self, visit: VisitData):
        """
        Initialize DashServer

        Args:
            visit (VisitData): VisitData object representing the current visit data including visualization data.
        """
        self.visit = visit
        self.visit_figures = []
        self.xray_names = []
        self.selected_figure_index = 0
        for visualization_data in self.visit.visualization_data_list:
            self.visit_figures.append(visualization_data.figure_creator.get_figure())
            self.xray_names.append(visualization_data.xray_filename.split("/")[-1].split(".")[0])
        self.current_figure = self.visit_figures[0]

        if self.visit.visualization_data_list[0].endoflip_screenshot:
            endoflip_table_width = '150px'
            show_pressure_endoflip_toggle = 'flex'
            endoflip_element = html.Div([
                    dcc.Graph(
                        id='endoflip-table',
                        figure=self.visit.visualization_data_list[0].figure_creator.get_endoflip_tables()['median'],
                        config={'modeBarButtonsToRemove': ['toImage'], 'displaylogo': False},className='mt-4',),
                    html.H6("Aggregationsform auswählen"),
                    dcc.Dropdown(
                        id='endoflip-table-dropdown',
                        options=[
                            {'label': 'Median', 'value': 'median'},
                            {'label': 'Mean', 'value': 'mean'},
                            {'label': 'Minimum', 'value': 'min'},
                            {'label': 'Maximum', 'value': 'max'},
                            {'label': 'Ausblenden', 'value': 'off'}
                        ],
                        value='median'  # Default value
                    ),   
                ],style={'height': 'calc(100vh - 160px)','width':endoflip_table_width, 'display': 'inline-block', 'verticalAlign': 'top', 'minWidth':endoflip_table_width})
        else:
            endoflip_table_width = '0px'
            show_pressure_endoflip_toggle = 'none'
            endoflip_element = None

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_bound = False
        for port in range(config.dash_port_range[0], config.dash_port_range[1] + 1):
            try:
                self.server_socket.bind(("127.0.0.1", port))
                self.port = port
                socket_bound = True
                break
            except:
                pass
        if not socket_bound:
            self.server_socket.close()
            QMessageBox.critical(None, "Fehler", "Keiner der in der Konfiguration angegebenen Ports ist verfügbar")
            return

        self.dash_app = DashProxy(__name__, prevent_initial_callbacks=True, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], transforms=[MultiplexerTransform()])
        self.dash_app.layout = html.Div([
            dcc.Interval(id='refresh-graph-interval', disabled=True,
                         interval=1000 / config.animation_frames_per_second),
            dcc.Store(id='color-store', data=self.visit.visualization_data_list[0].figure_creator.get_surfacecolor_list()),
            dcc.Store(id='tubular-metric-store', data=self.visit.visualization_data_list[0].figure_creator.get_metrics()[0]),
            dcc.Store(id='sphincter-metric-store', data=self.visit.visualization_data_list[0].figure_creator.get_metrics()[1]),
            dcc.Store(id='hidden-output'),

        
            html.Div([
                endoflip_element,
                dcc.Graph(
                    id='3d-figure',
                    figure=self.visit.visualization_data_list[0].figure_creator.get_figure(),
                    config={'modeBarButtonsToRemove': ['toImage','resetCameraLastSave3d'], 'displaylogo': False},
                    style={'height': 'calc(100vh - 160px)', 'width':f'calc(100% - {endoflip_table_width})', 'display': 'inline-block', 'minWidth':f'calc(100% - {endoflip_table_width})'}
                ),]),

            dbc.RadioItems(
                id='figure-selector',
                options=[{'label':  f'Breischluck {self.xray_names[i]}  ', 'value': i} for i in range(len(self.visit_figures))],
                value=0,
                inline=True,
                className="mb-1"
            ),

            html.Div([
                html.Div('Manometrie-Daten', style={'float': 'left', 'padding-left': '10px'}),
                daq.BooleanSwitch(id='pressure-or-endoflip', on=False), # False is Manometrie, True is Endoflip
                html.Div('Endoflip-Daten', style={'float': 'right', 'padding-right': '10px'}),
            ], style={'display': show_pressure_endoflip_toggle, 'align-items': 'center', 'padding-bottom': '5px'}),

            html.Div([
                html.Div([
                    html.Div(
                        dbc.Button('Animation starten', id='play-button', n_clicks=0),
                        style={'min-width': '130px', 'vertical-align': 'top', 'display': 'inline-block'}),
                    html.Div(
                        dcc.Slider(
                            min=0,
                            max=self.visit.visualization_data_list[0].figure_creator.get_number_of_frames() - 1,
                            step=1,
                            value=0,
                            marks=None,
                            id='time-slider',
                            updatemode='drag',
                            className='mt-2'
                        ),
                        style={'vertical-aling':'middle','align-items':'center', 'flex': '1 0 auto', 'display': 'inline-block'}
                    ),
                    html.Div(
                        id='time-field', children=' Zeitpunkt: 0.00s',
                        style={'min-width': '170px', 'display': 'inline-block'}
                    )
                ], style={'min-height': '30px', 'display': 'flex', 'align-items': 'center', 'flex-direction': 'row'}, id='pressure-control'),

                html.Div([
                    html.Div('30ml', style={'float': 'left', 'padding-left': '10px'}),
                    daq.BooleanSwitch(id='30-or-40', on=False), # False is 30, True is 40
                    html.Div('40ml',  style={'float': 'right', 'padding-right': '10px'}),
                ], style={'min-height': '30px', 'display': 'none', 'align-items': 'center', 'padding-bottom':'5px'}, id='endoflip-control'),

                html.Div(
                    id='metrics',
                    children="Metriken: tubulärer Abschnitt (" + str(config.length_tubular_part_cm) +
                             "cm) [Volumen*Druck]: " + str(round(self.visit.visualization_data_list[0].figure_creator.get_metrics()[0][0], 2)) +
                             "; unterer Sphinkter (" + str(self.visit.visualization_data_list[0].sphincter_length_cm) +
                             "cm) [Volumen/Druck]: " + str(round(self.visit.visualization_data_list[0].figure_creator.get_metrics()[1][0], 5))
                ),
            ])

        ], className='m-2', style={'height': '100%'})

        self.dash_app.clientside_callback(
            """
            function(time, index, figure, colors, tubular_metric, sphincter_metric, endoflip_on) {
                var expandedColors = [];
                if (!endoflip_on && colors !== null && colors[time] !== undefined && Array.isArray(colors[time])) {
                    for (var i = 0; i < colors[time].length; i++) {
                        expandedColors[i] = new Array(""" + str(config.figure_number_of_angles) + """).fill(colors[time][i]);
                        }
                        new_figure = {...figure};
                        new_figure.data[0].surfacecolor = expandedColors;
                        new_figure.data[0].colorscale = """ + str(config.colorscale) + """;
                        new_figure.data[0].cmin=""" + str(config.cmin) + """;
                        new_figure.data[0].cmax=""" + str(config.cmax) + """;
                        return [new_figure, 
                                "Zeitpunkt: " + (time/20).toFixed(2) + "s", 
                                "Metriken: tubulärer Abschnitt (""" + str(config.length_tubular_part_cm) + """cm) [Volumen*Druck]: " 
                                + tubular_metric[time].toFixed(2) + "; unterer Sphinkter (""" +
                                str(self.visit.visualization_data_list[self.selected_figure_index].sphincter_length_cm) + """cm) [Volumen/Druck]: " + sphincter_metric[time].toFixed(5)];
                    }
                }    
                """,
            [Output('3d-figure', 'figure'),
             Output('time-field', 'children'),
             Output('metrics', 'children')],
            [Input('time-slider', 'value'),
            Input('figure-selector', 'value'),
            Input('3d-figure', 'figure')],
            [State("color-store", "data"),
             State("tubular-metric-store", "data"),
             State("sphincter-metric-store", "data"), 
             State('pressure-or-endoflip','on')]
        )

        self.dash_app.callback([Output('pressure-control', 'style'), 
                                Output('endoflip-control', 'style'), 
                                Output('3d-figure', 'figure')], 
                                [Input('pressure-or-endoflip','on'),
                                 Input('endoflip-table-dropdown', 'value'),
                                 Input('30-or-40', 'on'),],
                                 State('3d-figure', 'figure'))(self.__toggle_pressure_endoflip)

        self.dash_app.callback([Output('endoflip-table','figure'), Output('endoflip-table','style')], Input('endoflip-table-dropdown', 'value'))(self.__update_endoflip_table)

        self.dash_app.callback([Output('refresh-graph-interval', 'disabled'),
                                Output('play-button', 'children'),
                                Output('time-slider', 'value')],
                               [Input('play-button', 'n_clicks')],
                               [State('refresh-graph-interval', 'disabled'),
                                State('time-slider', 'value'),
                                State('3d-figure', 'figure')])(self.__play_button_clicked_callback)

        self.dash_app.callback([Output('time-slider', 'value'),
                                Output('play-button', 'children'),
                                Output('refresh-graph-interval', 'disabled')],
                               [Input('refresh-graph-interval', 'n_intervals')],
                               [State('time-slider', 'value')])(self.__interval_action_callback)
        
        self.dash_app.callback([Output('3d-figure', 'figure'),
                                Output('color-store','data'), 
                                Output('tubular-metric-store','data'), 
                                Output('sphincter-metric-store','data'),
                                Output('time-slider', 'max'),
                                Output('metrics', 'children')],
                                Input('figure-selector', 'value'))(self.__update_figure)

        self.server = waitress.create_server(self.dash_app.server, sockets=[self.server_socket])
        self.thread = KThread(target=self.server.run)
        self.thread.start()

    def stop(self):
        """
        Stops the server and closes the socket.
        """
        self.thread.terminate()
        self.server_socket.close()

    def get_port(self):
        """
        Returns the port number of the server.

        Returns:
            int: Port number.
        """
        return self.port

    def __play_button_clicked_callback(self, n_clicks, disabled, value, figure):
        """
        Callback for the play button.

        Args:
            n_clicks (int): Number of clicks.
            disabled (bool): Disabled state of refresh-graph-interval.
            value (int): Time-slider value.

        Returns:
            tuple: New interval state, new button text, new slider value.
        """
        self.current_figure = go.Figure(figure)
        interval_new_state = not disabled
        slider_new_value = no_update
        if interval_new_state:
            button_text = DashServer.button_text_start
        else:
            button_text = DashServer.button_text_stop
            if value == self.visit.visualization_data_list[self.selected_figure_index].figure_creator.get_number_of_frames() - 1:
                slider_new_value = 0
        return interval_new_state, button_text, slider_new_value

    def __interval_action_callback(self, n_intervals, value):
        """
        Callback for refresh-graph-interval.

        Args:
            n_intervals (int): Number of intervals.
            value (int): Slider value.

        Returns:
            tuple: New slider value, new button text, new slider disabled state.
        """
        new_value = value + int(config.csv_values_per_second / config.animation_frames_per_second)
        if new_value >= self.visit.visualization_data_list[self.selected_figure_index].figure_creator.get_number_of_frames() - 1:
            return self.visit.visualization_data_list[self.selected_figure_index].figure_creator.get_number_of_frames() - 1, DashServer.button_text_start, True
        else:
            return new_value, no_update, no_update
    

    def __update_figure(self,selected_figure):
        """
        Callback to update the figure and related components.

        Args:
            selected_figure (int): Selected figure index.

        Returns:
            list: Updated figure, color store, tubular metric store, sphincter metric store, maximum value of time slider, updated time slider value, metrics text.
        """
        self.selected_figure_index = selected_figure
        self.current_figure = self.visit_figures[selected_figure]
        if selected_figure is not None:
            return [self.visit_figures[selected_figure], 
                    self.visit.visualization_data_list[selected_figure].figure_creator.get_surfacecolor_list(),
                    self.visit.visualization_data_list[selected_figure].figure_creator.get_metrics()[0],
                    self.visit.visualization_data_list[selected_figure].figure_creator.get_metrics()[1],
                    self.visit.visualization_data_list[selected_figure].figure_creator.get_number_of_frames() - 1,
                    "Metriken: tubulärer Abschnitt (" + str(config.length_tubular_part_cm) +
                             "cm) [Volumen*Druck]: " + str(round(self.visit.visualization_data_list[selected_figure].figure_creator.get_metrics()[0][0], 2)) +
                             "; unterer Sphinkter (" + str(self.visit.visualization_data_list[selected_figure].sphincter_length_cm) +
                             "cm) [Volumen/Druck]: " + str(round(self.visit.visualization_data_list[selected_figure].figure_creator.get_metrics()[1][0], 5))]
        else:
            raise PreventUpdate
        
    def __toggle_pressure_endoflip(self, endoflip_selected, aggregate_function, ballon_volume, figure):
        """
        Callback to toggle between pressure and Endoflip visualization and update aggregate function/ballon volume visualization of EndoFLIP.

        Args:
            endoflip_selected (bool): True if Endoflip data is selected, False for pressure data.
            figure (dict): Current figure dictionary.
            aggregate_function (str): The aggregation function for Endoflip data.
            ballon_volume (bool): True for 40ml balloon, False for 30ml balloon.

        Returns:
            tuple: Pressure control style, Endoflip control style, updated figure.
        """
        if not endoflip_selected:
            # Surface color is changed back to pressure values automatically due to animation
            return {'min-height': '30px', 'display': 'flex', 'flex-direction': 'row'}, {'display': 'none', 'align-items': 'center'}, self.visit_figures[self.selected_figure_index]
        else:
            # Get endoflip surfacecolors
            endoflip_color = self.visit.visualization_data_list[self.selected_figure_index].figure_creator.get_endoflip_surface_color('40' if ballon_volume else '30', aggregate_function)
            expandedColors = [[endoflip_color[i] for _ in range(config.figure_number_of_angles)] for i in range(len(endoflip_color))]
            figure = go.Figure(figure)
            figure.data[0].surfacecolor = expandedColors
            figure.data[0].colorscale = px.colors.sample_colorscale("jet", [(30-(n+1))/(30-1) for n in range(30)])
            figure.data[0].cmin= 0
            figure.data[0].cmax= 30
            self.current_figure = figure
            return {'min-height': '30px', 'display': 'none', 'flex-direction': 'row'}, {'display': 'flex', 'align-items': 'center'}, figure
        
    def __update_endoflip_table(self, chosen_agg):
        """
        Callback to update the Endoflip color projection on figure and Endoflip table.

        Args:
            chosen_agg (str): The chosen Endoflip aggregation function.

        Returns:
            tuple: Updated Endoflip figure, Endoflip table style.
        """
        if chosen_agg == 'off':
            return self.visit.visualization_data_list[0].figure_creator.get_endoflip_tables()['median'], {'display':'none'}
        else:
            return self.visit.visualization_data_list[0].figure_creator.get_endoflip_tables()[chosen_agg], {'display':'block'}
        
