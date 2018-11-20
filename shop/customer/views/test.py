# coding: utf-8
import StringIO
import decimal
import json
import string
import random

import requests
from faker import Factory
from locust import HttpLocust, TaskSet, task
import csv


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


products = list(csv.DictReader(StringIO.StringIO(requests.get(
    "https://gist.githubusercontent.com/buremba/f1299b848e081519990c/raw/c79c618b95ceee66ee50d4877bbc669abd49c314/gistfile1.txt").text),
                               delimiter=";"))
user_agents = requests.get(
    "https://gist.githubusercontent.com/buremba/a005e893fa3bf88f9951/raw/977fa942fe20a1c9115b68e50db2b0988fde0d29/gistfile1.json").json()

session_generator = lambda: ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
platform_generator = lambda: ["desktop", "mobile", "tablet"][random.randint(0, 2)]
social_source_generator = lambda: ["facebook", "twitter", "google"][random.randint(0, 2)]
search_engine_generator = lambda: ["google", "google", "google", "bing", "bing", "yandex", "yahoo"][
    random.randint(0, 6)]
brand_generator = lambda: ["Audi", "BMW", "Renault", "Chevrolet"][
    random.randint(0, 3)]
category_generator = lambda: ["Aydınlatma", "Tampon", "Yakıt", "Yağlar", 'Amortisor', 'Aktarma'][
    random.randint(0, 5)]
brand_model_generator = lambda: ["A3", "A4", "Clio", "X5", 'X6'][
    random.randint(0, 4)]
manufacturer_generator = lambda: ["Dega", "Kombo", "Tombo", "Cyrser", 'Olimpos'][
    random.randint(0, 4)]
resolution_generator = lambda: ["1920 x 1080", "800 x 600"][
    random.randint(0, 2)]

sorting_generator = lambda: ["price", "name", "random", "popular"][random.randint(0, 3)]
fake = Factory.create()

project = "shop3"


def post_event_data(client, collection, properties):
    return client.post("/event/collect",
                       data=json.dumps({'project': project, 'collection': collection, 'properties': properties},
                                       default=decimal_default))
users = range(100000)

class WebsiteTasks(TaskSet):

    @task(4)
    def register_event(self):
        data = {'email': fake.email(), 'name': fake.name(), 'address': fake.address(), 'age': 15 + random.randint(0, 20),
                "country_code": fake.country_code(), "ip": fake.ipv4(), "company": fake.company(),
                "company_type": fake.company_suffix(), "timezone": fake.timezone()}

        user = self.client.post("/user/create",
                                data=json.dumps({'project': project, 'properties': data}, default=decimal_default))
        if user.status_code == 200:
            user_id = user.json().get('identifier')
            users.append(str(user_id))
            data['_user'] = user_id
            post_event_data(self.client, "register", data)

    @task(5)
    def basket_product(self):
        return post_event_data(self.client, "add_basket", {
            '_user': random.choice(users),
            'partner_code': random.randint(0, 1000)+"STOCK",
            "price": random.randint(0, 300),
            "manufacturer": manufacturer_generator(),
            "count": random.randint(0, 10),
        })

        if random.randint(0, 10) > 5:
            post_event_data(self.client, "order", {
                '_user': random.choice(users),
                'product_sku': product["id"],
                'product_name': product["name"],
                "product_price": float(product["price"]),
                "product_manufacturer": product["manufacturer"],
                "count": random.randint(0, 10),
                "ip": fake.ipv4(),
            })

    @task(7)
    def search_event(self):
        user = random.choice(users)
        returning_session = True if random.randint(0, 10) > 7 else False
        return post_event_data(self.client, "search", {
            '_user': user,
            'platform': 'Web',
            'device_id': user,
            'session_id': int(user),
            'brand': brand_generator(),
            'brand_model': brand_model_generator(),
            'category': category_generator(),
            'session_id': int(user),
            'category': category_generator(),
            '_user_agent': random.choice(user_agents),
            'sorting': sorting_generator(),
            'language': 'TR-tr',
            'page': random.randint(0, 10),
            '_ip': fake.ipv4(),
            'returning_session': returning_session,
            'time_on_page': random.randint(0, 100) if returning_session else None
        })

    @task(7)
    def page_view(self):
        user = random.choice(users)
        returning_session = True if random.randint(0, 10) > 7 else False
        return post_event_data(self.client, "pageview", {
            '_user': user,
            'platform': 'Web',
            'device_id': user,
            'session_id': int(user),
            '_user_agent': random.choice(user_agents),
            'sorting': sorting_generator(),
            'language': 'TR-tr',
            'page': random.randint(0, 10),
            '_ip': fake.ipv4(),
            'color_depth': "24bit",
            'resolution': resolution_generator(),
            'title': " ".join(fake.words()),
            'lang': 'Turkish',
            'returning_session': returning_session,
            'time_on_page': random.randint(0, 100) if returning_session else None
        })

    @task(7)
    def view_product(self):
        user = random.choice(users)
        returning_session = True if random.randint(0, 10) > 7 else False
        return post_event_data(self.client, "view_product", {
            '_user': user,
            'platform': 'Web',
            'device_id': user,
            'path': fake.uri_path(),
            'session_id': int(user),
            'price': random.randint(0, 1000),
            '_user_agent': random.choice(user_agents),
            'partner_code': random.randint(0, 1000)+"STOCK",
            'manufacturer': manufacturer_generator(),
            'language': fake.locale(),
            '_ip': fake.ipv4(),
            'returning_session': returning_session,
            'time_on_page': random.randint(0, 100) if returning_session else None
        })

    @task(2)
    def order(self):
        user = random.choice(users)
        returning_session = True if random.randint(0, 10) > 7 else False
        return post_event_data(self.client, "order", {
            '_user': user,
            'platform': 'Web',
            'product_count': random.randint(0, 3),
            'total_price': random.randint(0, 3000),
            'device_id': user,
            'session_id': int(user),
            '_user_agent': random.choice(user_agents),
            'language': fake.locale(),
            '_ip': fake.ipv4(),
        })

class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    min_wait = 5000
    max_wait = 15000