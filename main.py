import view

from app import app

from realty_parser.models import ItemsDB

if __name__ == '__main__':
    db = ItemsDB()
    db.create_db()
    app.run(host='0.0.0.0', port=5000)

