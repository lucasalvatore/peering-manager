from rest_framework.routers import APIRootView

from .as_path import *
from .community import *
from .prefix_list import *
from .relationship import *


class BGPRootView(APIRootView):
    def get_view_name(self):
        return "BGP"
