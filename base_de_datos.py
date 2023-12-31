"""
Json store master
"""

import json


class BaseDeDatos():
    """
    Json store master
    """
    
    _data_list = []
    __ERROR_MESSAGE_PATH = "Wrong file or file path"
    __ERROR_JSON_DECODE = "JSON Decode Error - Wrong JSON Format"
    FILE_PATH = ""
    ID_FIELD = ""

    def __init__(self):
        self.load_store()
    
    def save_store(self):
        try:
            with open(self.FILE_PATH, "w", encoding="utf-8", newline="") as file:
                json.dump(self._data_list, file, indent=2)
        except FileNotFoundError as ex:
            #raise OrderManagementException(self.__ERROR_MESSAGE_PATH) from ex
            print("FileNotFoundError")

    def find_data(self, data_to_find):
        self.load_store()
        item_found = None
        for item in self._data_list:
            if item[self.ID_FIELD] == data_to_find:
                item_found = item
        return item_found

    def load_store(self):
        """
        load store
        """
        try:
            with open(self.FILE_PATH, "r", encoding="utf-8", newline="") as file:
                self._data_list = json.load(file)
        except FileNotFoundError:
            # file is not found , so  init my data_list
            self._data_list = []


    def add_item(self, item: any):
        """
        add item
        """
        self.load_store()
        self._data_list.append(item)
        self.save_store()

