import socket
import waitress
from PyQt5.QtWidgets import QMessageBox
from dash_extensions.enrich import Input, Output, State, DashProxy, MultiplexerTransform, html, dcc, no_update
from kthread import KThread
import config
import os
from logic.visualization_data import VisualizationData


class DashServer:
    """Represents the dash server that is needed for the visualization"""

    button_text_start = 'Animation starten'
    button_text_stop = 'Animation anhalten'

    def __init__(self, all_visualization):
        """
        init DashServer
        :param visualization_data: VisualizationData
        """
        self.all_visualization = all_visualization.copy()

        # radio_text1 = os.path.splitext(os.path.basename(self.all_visualization[0].xray_filename))[0]
        # print(radio_text1)
        # if len(self.all_visualization) > 1:
        #     radio_text2 = os.path.splitext(os.path.basename(self.all_visualization[1].xray_filename))[0]
        # else:
        #     radio_text2 = "--"
        # print(radio_text2)
        # if len(self.all_visualization) > 2:
        #     radio_text3 = os.path.splitext(os.path.basename(self.all_visualization[2].xray_filename))[0]
        # else:
        #     radio_text3 = "--"
        # print(radio_text3)

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
            dcc.Store(id='color-store', data=self.all_visualization[0].figure_creator.get_surfacecolor_list()),
            dcc.Store(id='tubular-metric-store', data=self.all_visualization[0].figure_creator.get_metrics()[0]),
            dcc.Store(id='sphincter-metric-store', data=self.all_visualization[0].figure_creator.get_metrics()[1]),

            dcc.Graph(
                id='3d-figure',
                figure=self.all_visualization[0].figure_creator.get_figure(),
                config={'modeBarButtonsToRemove': ['toImage', 'resetCameraLastSave3d'], 'displaylogo': False},
                style={'height': 'calc(100% - 60px)'}
            ),
            html.Div([
                dcc.Input(id='sphincter_length', type='hidden', value=self.all_visualization[0].sphincter_length_cm),
                html.Div([
                    html.Div(
                        html.Button('Animation starten', id='play-button', n_clicks=0),
                        style={'min-width': '130px', 'vertical-align': 'top', 'display': 'inline-block'}
                    ),
                    html.Div(
                        dcc.Slider(
                            min=0,
                            max=self.all_visualization[0].figure_creator.get_number_of_frames() - 1 if self.all_visualization[0].figure_creator.get_number_of_frames() > 0 else 0,
                            step=1,
                            value=0,
                            marks=None,
                            id='time-slider',
                            updatemode='drag'
                        ),
                        style={'vertical-align': 'top', 'flex': '1 0 auto', 'display': 'inline-block'}
                    ),
                    html.Div(
                        id='time-field',
                        children=' Zeitpunkt: 0.00s',
                        style={'min-width': '170px', 'vertical-align': 'top', 'display': 'inline-block'}
                    ),
                ], style={'min-height': '40px', 'display': 'flex', 'flex-direction': 'row'}),
                html.Div(
                    id='metrics',
                    children="Metriken: tubulärer Abschnitt (" + str(config.length_tubular_part_cm) +
                             "cm) [Volumen*Druck]: " + str(
                        round(self.all_visualization[0].figure_creator.get_metrics()[0][0], 2)) +
                             "; unterer Sphinkter (" + str(self.all_visualization[0].sphincter_length_cm) +
                             "cm) [Volumen/Druck]: " + str(
                        round(self.all_visualization[0].figure_creator.get_metrics()[1][0], 5))
                ),
                html.Div(
                    children="Wähle Breischluckbild:",
                    style={'font-weight': 'bold'}
                ),
                html.Div(
                    id='radio-buttons-container',
                    children=[
                        html.Div(
                            dcc.RadioItems(
                                id='radio-buttons',
                                options=[],
                                value='0',
                                labelStyle={'display': 'inline-block', 'padding': '5px'}
                            ),
                            style={'vertical-align': 'top', 'display': 'inline-block'}
                        ),
                    ]
                ),
                html.Div(
                    id="description",
                    children=[]
                )
            ])

        ], style={'height': 'calc(100vh - 20px)'})

        self.dash_app.clientside_callback(
            """
            function(time, figure, colors, tubular_metric, sphincter_metric, sphincter_length) {
                var expandedColors = [];
                for (var i = 0; i < colors[time].length; i++) {
                    expandedColors[i] = new Array(""" + str(config.figure_number_of_angles) + """).fill(colors[time][i]);
                    }
                    new_figure = {...figure};
                    new_figure.data[0].surfacecolor = expandedColors;
                    return [new_figure, "Zeitpunkt: " + (time/20).toFixed(2) + "s", "Metriken: tubulärer Abschnitt (""" +
            str(config.length_tubular_part_cm) + """cm) [Volumen*Druck]: " + tubular_metric[time].toFixed(2) + "; unterer Sphinkter (" """ +
            """+ sphincter_length.toFixed(2) +"cm) [Volumen/Druck]: " + sphincter_metric[time].toFixed(5)];
                }
                """,
            [Output('3d-figure', 'figure'),
             Output('time-field', 'children'),
             Output('metrics', 'children')],
            Input('time-slider', 'value'),
            [State('3d-figure', 'figure'),
             State("color-store", "data"),
             State("tubular-metric-store", "data"),
             State("sphincter-metric-store", "data"),
             State('sphincter_length', 'value')]
        )

        self.dash_app.callback([Output('refresh-graph-interval', 'disabled'),
                                Output('play-button', 'children'),
                                Output('time-slider', 'value'),
                                Output('color-store', 'data'),
                                Output('tubular-metric-store', 'data'),
                                Output('sphincter-metric-store', 'data'),
                                Output('3d-figure', 'figure'),
                                Output('time-slider', 'max'),
                                Output('metrics', 'children'),
                                Output('sphincter_length', 'value'),
                                Output('description', 'children')],
                               [Input('radio-buttons', 'value')]
                               )(self.__switch_visualization_callback)

        self.dash_app.callback([Output('refresh-graph-interval', 'disabled'),
                                Output('play-button', 'children'),
                                Output('time-slider', 'value')],
                               [Input('play-button', 'n_clicks')],
                               [State('refresh-graph-interval', 'disabled'),
                                State('time-slider', 'value'),
                                State('radio-buttons', 'value')])(self.__play_button_clicked_callback)

        self.dash_app.callback([Output('time-slider', 'value'),
                                Output('play-button', 'children'),
                                Output('refresh-graph-interval', 'disabled')],
                               [Input('refresh-graph-interval', 'n_intervals')],
                               [State('time-slider', 'value'),
                                State('radio-buttons', 'value')])(self.__interval_action_callback)

        self.server = waitress.create_server(self.dash_app.server, sockets=[self.server_socket])
        self.thread = KThread(target=self.server.run)
        self.thread.start()
        #self.update_radio_buttons()

    def update_radio_buttons(self):
        print("update radio buttons")
        radio_options = [
            {'label': os.path.splitext(os.path.basename(vis.xray_filename))[0], 'value': str(i)}
            for i, vis in enumerate(self.all_visualization)
        ]
        self.dash_app.layout['radio-buttons-container'] = {
            'children': [
                html.Div(
                    dcc.RadioItems(
                        id='radio-buttons',
                        options=radio_options,
                        value='0',
                        labelStyle={'display': 'inline-block', 'padding': '5px'}
                    ),
                    style={'vertical-align': 'top', 'display': 'inline-block'}
                ),
            ]
        }

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

    def __switch_visualization_callback(self, value):

        value = int(value)
        color_store = self.all_visualization[value].figure_creator.get_surfacecolor_list()
        tubular_metric_store = self.all_visualization[value].figure_creator.get_metrics()[0]
        sphincter_metric_store = self.all_visualization[value].figure_creator.get_metrics()[1]
        figure = self.all_visualization[value].figure_creator.get_figure()
        time_slider = self.all_visualization[value].figure_creator.get_number_of_frames() - 1
        metrics = f"Metriken: tubulärer Abschnitt ({config.length_tubular_part_cm} cm) " \
                  f"[Volumen*Druck]: ({round(self.all_visualization[value].figure_creator.get_metrics()[0][0], 2)}); " \
                  f"unterer Sphinkter ({self.all_visualization[value].sphincter_length_cm} cm) " \
                  f"[Volumen/Druck]: ({round(self.all_visualization[value].figure_creator.get_metrics()[1][0], 5)})"
        sphincter_length = self.all_visualization[value].sphincter_length_cm
        description = f"Bild: {self.all_visualization[value].xray_filename} ausgewählt"

        return True, 'Animation starten', 0, color_store, tubular_metric_store, sphincter_metric_store, figure, \
            time_slider, metrics, sphincter_length, description

    def __play_button_clicked_callback(self, n_clicks, disabled, value, value_radio):
        """
        callback of the play button
        :param n_clicks: number of clicks
        :param disabled: disabled state of refresh-graph-interval
        :param value: time-slider value
        :return: new interval state, new button text, new slider value
        """
        value_radio = int(value_radio)
        interval_new_state = not disabled
        slider_new_value = no_update
        if interval_new_state:
            button_text = DashServer.button_text_start
        else:
            button_text = DashServer.button_text_stop
            if value == self.all_visualization[value_radio].figure_creator.get_number_of_frames() - 1:
                slider_new_value = 0
        return interval_new_state, button_text, slider_new_value

    def __interval_action_callback(self, n_intervals, value, value_radio):
        """
        callback of refresh-graph-interval
        :param n_intervals: number of intervals
        :param value: slider value
        :return: new slider value, new button text, new slider disabled state
        """
        value_radio = int(value_radio)
        new_value = value + int(config.csv_values_per_second / config.animation_frames_per_second)
        if new_value >= self.all_visualization[value_radio].figure_creator.get_number_of_frames() - 1:
            return self.all_visualization[
                       value_radio].figure_creator.get_number_of_frames() - 1, DashServer.button_text_start, True
        else:
            return new_value, no_update, no_update
