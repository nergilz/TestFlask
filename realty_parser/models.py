from peewee import (MySQLDatabase, Model, IntegerField, CharField, DateField, TextField,
                    FloatField, DoesNotExist, InternalError)

db = MySQLDatabase(database='realty',
                   user='root',
                   password='oruri448', threadlocals=True, host='mysql', port=3306)


class CianModel(Model):
    class Meta:
        database = db


class ItemsDB(CianModel):
    url = CharField()
    site = CharField()
    price = IntegerField(null=True)
    price_per_meter = IntegerField(null=True)
    rooms = CharField(null=True)
    total_square = FloatField(null=True)
    rooms_square = CharField(null=True)
    living_square = CharField(null=True)
    kitchen_square = CharField(null=True)
    wc = CharField(null=True)
    balcony = CharField(null=True)
    elevator = CharField(null=True)
    parking = CharField(null=True)
    window_look = CharField(null=True)
    issue_date = CharField(null=True)
    house_type = CharField(null=True)
    matherial_type = CharField(null=True)
    floor = CharField(null=True)
    floors = CharField(null=True)
    type_salary = CharField(null=True)
    region = CharField(null=True)
    city = CharField(null=True)
    district = CharField(null=True)
    microdistrict = CharField(null=True)
    street = CharField(null=True)
    house_num = CharField(null=True)
    JK_name = CharField(null=True)
    seller_phone = CharField(null=True)
    premium_status = CharField(null=True)
    publish_date = DateField(null=True)
    up_date = CharField(null=True)
    decoration = CharField(null=True)
    ad_text = TextField(null=True)
    views = CharField(null=True)

    def create_db(self):
        try:
            db.create_table(ItemsDB)
        except InternalError:
            pass

    @db.execution_context(with_transaction=False)
    def add_item(self, **kwargs):
        if not self.search_item(url=kwargs['url']):
            new_item = ItemsDB.create(**kwargs)
            ItemsDB.save(new_item)
        else:
            new_item = ItemsDB.get(url=kwargs['url'])
            new_item.price = kwargs['price']
            new_item.price_per_meter = kwargs['price_per_meter']
            new_item.issue_date = kwargs['issue_date']
            new_item.type_salary = kwargs['type_salary']
            new_item.seller_phone = kwargs['seller_phone']
            new_item.premium_status = kwargs['premium_status']
            new_item.up_date = kwargs['up_date']
            new_item.ad_text = kwargs['ad_text']
            ItemsDB.save(new_item)

    def search_item(self, url):
        try:
            return ItemsDB.get(ItemsDB.url == url)
        except DoesNotExist:
            return None

