import os
import socket

import config
import plotly.graph_objects as go
import waitress
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import (DashProxy, Input, MultiplexerTransform,
                                    Output, State, dcc, html, no_update)
from kthread import KThread
from logic.visit_data import VisitData
from logic.visualization_data import VisualizationData
from PyQt5.QtWidgets import QMessageBox


class DashServer:
    """Represents the dash server that is needed for the visualization"""

    button_text_start = 'Animation starten'
    button_text_stop = 'Animation anhalten'

    def __init__(self, visit: VisitData):
        """
        Initialize DashServer

        Args:
            visit (VisitData): VisitData object
        """
        self.visit = visit
        self.visit_figures = []
        self.selected_figure_index = 0
        for visualization_data in self.visit.visualization_data_list:
            self.visit_figures.append(visualization_data.figure_creator.get_figure())
        self.current_figure = self.visit_figures[0]

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

        self.dash_app = DashProxy(__name__, prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])
        self.dash_app.layout = html.Div([
            dcc.Interval(id='refresh-graph-interval', disabled=True,
                         interval=1000 / config.animation_frames_per_second),
            dcc.Store(id='color-store', data=self.visit.visualization_data_list[0].figure_creator.get_surfacecolor_list()),
            dcc.Store(id='tubular-metric-store', data=self.visit.visualization_data_list[0].figure_creator.get_metrics()[0]),
            dcc.Store(id='sphincter-metric-store', data=self.visit.visualization_data_list[0].figure_creator.get_metrics()[1]),

            dcc.Graph(
                id='3d-figure',
                figure=self.visit.visualization_data_list[0].figure_creator.get_figure(),
                config={'modeBarButtonsToRemove': ['toImage', 'resetCameraLastSave3d'], 'displaylogo': False},
                style={'height': 'calc(100vh - 110px)'}
            ),

            dcc.RadioItems(
                id='figure-selector',
                options=[{'label':  f'Breischluck {i+1}  ', 'value': i} for i in range(len(self.visit_figures))],
                value=0,
                inline=True,
                className="mb-1"
            ),

            html.Div([
                html.Div([
                    html.Div(
                        html.Button('Animation starten', id='play-button', n_clicks=0),
                        style={'min-width': '130px', 'vertical-align': 'top', 'display': 'inline-block'}),
                    html.Div(
                        dcc.Slider(
                            min=0,
                            max=self.visit.visualization_data_list[0].figure_creator.get_number_of_frames() - 1,
                            step=1,
                            value=0,
                            marks=None,
                            id='time-slider',
                            updatemode='drag'
                        ),
                        style={'vertical-align': 'top', 'flex': '1 0 auto', 'display': 'inline-block'}
                    ),
                    html.Div(
                        id='time-field', children=' Zeitpunkt: 0.00s',
                        style={'min-width': '170px', 'vertical-align': 'top', 'display': 'inline-block'}
                    )
                ], style={'min-height': '30px', 'display': 'flex', 'flex-direction': 'row'}),
                html.Div(
                    id='metrics',
                    children="Metriken: tubulärer Abschnitt (" + str(config.length_tubular_part_cm) +
                             "cm) [Volumen*Druck]: " + str(round(self.visit.visualization_data_list[0].figure_creator.get_metrics()[0][0], 2)) +
                             "; unterer Sphinkter (" + str(self.visit.visualization_data_list[0].sphincter_length_cm) +
                             "cm) [Volumen/Druck]: " + str(round(self.visit.visualization_data_list[0].figure_creator.get_metrics()[1][0], 5))
                ),
            ])

        ], style={'height': '100vh'})

        self.dash_app.clientside_callback(
            """
            function(time, index, figure, colors, tubular_metric, sphincter_metric) {
                var expandedColors = [];
                for (var i = 0; i < colors[time].length; i++) {
                    expandedColors[i] = new Array(""" + str(config.figure_number_of_angles) + """).fill(colors[time][i]);
                    }
                    new_figure = {...figure};
                    new_figure.data[0].surfacecolor = expandedColors;
                    return [new_figure, 
                            "Zeitpunkt: " + (time/20).toFixed(2) + "s", 
                            "Metriken: tubulärer Abschnitt (""" + str(config.length_tubular_part_cm) + """cm) [Volumen*Druck]: " 
                            + tubular_metric[time].toFixed(2) + "; unterer Sphinkter (""" +
                            str(self.visit.visualization_data_list[self.selected_figure_index].sphincter_length_cm) + """cm) [Volumen/Druck]: " + sphincter_metric[time].toFixed(5)];
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
             State("sphincter-metric-store", "data"),]
        )

        self.dash_app.callback(Output('3d-figure', 'figure'),Input('3d-figure','figure'))(self.__get_current_figure_callback)

        self.dash_app.callback([Output('refresh-graph-interval', 'disabled'),
                                Output('play-button', 'children'),
                                Output('time-slider', 'value')],
                               [Input('play-button', 'n_clicks')],
                               [State('refresh-graph-interval', 'disabled'),
                                State('time-slider', 'value')])(self.__play_button_clicked_callback)

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
        stops the server
        """
        self.thread.terminate()
        self.server_socket.close()

    def get_port(self):
        """
        returns the port of the server
        :return: port number
        """
        return self.port

    def __play_button_clicked_callback(self, n_clicks, disabled, value):
        """
        Callback of the play button

        Args:
            n_clicks (int): Number of clicks
            disabled (bool): Disabled state of refresh-graph-interval
            value (int): Time-slider value

        Returns:
            tuple: New interval state, new button text, new slider value
        """
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
        Callback of refresh-graph-interval

        Args:
            n_intervals (int): Number of intervals
            value (int): Slider value

        Returns:
            tuple: New slider value, new button text, new slider disabled state
        """
        new_value = value + int(config.csv_values_per_second / config.animation_frames_per_second)
        if new_value >= self.visit.visualization_data_list[self.selected_figure_index].figure_creator.get_number_of_frames() - 1:
            return self.visit.visualization_data_list[self.selected_figure_index].figure_creator.get_number_of_frames() - 1, DashServer.button_text_start, True
        else:
            return new_value, no_update, no_update
        
    
    def __get_current_figure_callback(self,figure):
        """
        Callback to update self.current_figure

        Args:
            figure (dict): Dict from Graph object

        Returns:
            dict: Figure unchanged (without returning the figure, it won't update again)
        """
        self.current_figure = go.Figure(figure)
        return self.current_figure
    

    def __update_figure(self,selected_figure):
        """
        Callback to update the figure and related components

        Args:
            selected_figure (int): Selected figure index

        Returns:
            list: Updated figure, color store, tubular metric store, sphincter metric store,
                  maximum value of time slider, updated time slider value, metrics text
        """
        self.selected_figure_index = selected_figure
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