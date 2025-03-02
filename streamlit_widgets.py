import streamlit as st
from abc import ABC, abstractmethod

class Widget(ABC):
    @property
    def name(self):
        pass

    @property
    def description(self):
        pass

    @property
    def params(self):
        pass

    @abstractmethod
    def display(self, params):
        pass

class MapWidget(Widget):
    name = "map"
    description = "Displays a map"
    params = {
        "latitude": "List of latitudes for display",
        "longitude": "List of longitudes for display"
    }

    def display(self, params):
        st.map(data={
            "latitude": params["latitude"],
            "longitude": params["longitude"]
        })


class MetricWidget(Widget):
    name = "metric"
    description = "Displays a metric, i.e. temperature, humidity, etc."
    params = {
        "metric_name": "List of metric names to display",
        "value": "List of values to display"
    }

    def display(self, params):
        cols = st.columns(len(params["metric_name"]))
        for i, col in enumerate(cols):
            col.metric(params["metric_name"][i], params["value"][i])
