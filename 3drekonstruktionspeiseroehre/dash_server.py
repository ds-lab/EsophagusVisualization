import socket
import waitress
from PyQt5.QtWidgets import QMessageBox
from dash_extensions.enrich import Input, Output, State, DashProxy, MultiplexerTransform, html, dcc, no_update
from kthread import KThread
import config
from logic.visualization_data import VisualizationData
import plotly.graph_objects as go


class DashServer:
    """Represents the dash server that is needed for the visualization"""

    button_text_start = 'Animation starten'
    button_text_stop = 'Animation anhalten'

    def __init__(self, visualization_data: VisualizationData):
        """
        init DashServer
        :param visualization_data: VisualizationData
        """
        self.visualization_data = visualization_data
        self.figure = self.visualization_data.figure_creator.get_figure()
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
            dcc.Store(id='color-store', data=visualization_data.figure_creator.get_surfacecolor_list()),
            dcc.Store(id='tubular-metric-store', data=visualization_data.figure_creator.get_metrics()[0]),
            dcc.Store(id='sphincter-metric-store', data=visualization_data.figure_creator.get_metrics()[1]),
           
            dcc.Graph(
                id='3d-figure',
                figure=visualization_data.figure_creator.get_figure(),
                config={'modeBarButtonsToRemove': ['toImage', 'resetCameraLastSave3d'], 'displaylogo': False},
                style={'height': 'calc(100% - 60px)'}
            ),
            html.Div([
                html.Div([
                    html.Div(
                        html.Button('Animation starten', id='play-button', n_clicks=0),
                        style={'min-width': '130px', 'vertical-align': 'top', 'display': 'inline-block'}),
                    html.Div(
                        dcc.Slider(
                            min=0,
                            max=visualization_data.figure_creator.get_number_of_frames() - 1,
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
                ], style={'min-height': '40px', 'display': 'flex', 'flex-direction': 'row'}),
                html.Div(
                    id='metrics',
                    children="Metriken: tubulärer Abschnitt (" + str(config.length_tubular_part_cm) +
                             "cm) [Volumen*Druck]: " + str(round(visualization_data.figure_creator.get_metrics()[0][0], 2)) +
                             "; unterer Sphinkter (" + str(visualization_data.sphincter_length_cm) +
                             "cm) [Volumen/Druck]: " + str(round(visualization_data.figure_creator.get_metrics()[1][0], 5))
                ),
            ])

        ], style={'height': 'calc(100vh - 20px)'})

        self.dash_app.clientside_callback(
            """
            function(time, figure, colors, tubular_metric, sphincter_metric) {
                var expandedColors = [];
                for (var i = 0; i < colors[time].length; i++) {
                    expandedColors[i] = new Array(""" + str(config.figure_number_of_angles) + """).fill(colors[time][i]);
                    }
                    new_figure = {...figure};
                    new_figure.data[0].surfacecolor = expandedColors;
                    return [new_figure, "Zeitpunkt: " + (time/20).toFixed(2) + "s", "Metriken: tubulärer Abschnitt (""" +
            str(config.length_tubular_part_cm) + """cm) [Volumen*Druck]: " + tubular_metric[time].toFixed(2) + "; unterer Sphinkter (""" +
            str(visualization_data.sphincter_length_cm) + """cm) [Volumen/Druck]: " + sphincter_metric[time].toFixed(5)];
                }
                """,
            [Output('3d-figure', 'figure'),
             Output('time-field', 'children'),
             Output('metrics', 'children')],
            Input('time-slider', 'value'),
            [State('3d-figure', 'figure'),
             State("color-store", "data"),
             State("tubular-metric-store", "data"),
             State("sphincter-metric-store", "data")]
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
        callback of the play button
        :param n_clicks: number of clicks
        :param disabled: disabled state of refresh-graph-interval
        :param value: time-slider value
        :return: new interval state, new button text, new slider value
        """
        interval_new_state = not disabled
        slider_new_value = no_update
        if interval_new_state:
            button_text = DashServer.button_text_start
        else:
            button_text = DashServer.button_text_stop
            if value == self.visualization_data.figure_creator.get_number_of_frames() - 1:
                slider_new_value = 0
        return interval_new_state, button_text, slider_new_value

    def __interval_action_callback(self, n_intervals, value):
        """
        callback of refresh-graph-interval
        :param n_intervals: number of intervals
        :param value: slider value
        :return: new slider value, new button text, new slider disabled state
        """
        new_value = value + int(config.csv_values_per_second / config.animation_frames_per_second)
        if new_value >= self.visualization_data.figure_creator.get_number_of_frames() - 1:
            return self.visualization_data.figure_creator.get_number_of_frames() - 1, DashServer.button_text_start, True
        else:
            return new_value, no_update, no_update
        
    
    def __get_current_figure_callback(self,figure):
        """
        callback to update self.figure
        :param figure: dict from Graph object
        :return: figure unchanged (without return the figure does not update again)
        """
        self.figure = go.Figure(figure)
        return self.figure

    