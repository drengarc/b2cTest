class BasketItemInsufficientStock(Exception):
    def __init__(self, product, *args, **kwargs):
        self.product = product


class BasketItemNotExist(Exception):
    def __init__(self, product, *args, **kwargs):
        self.product = product