import json
from unittest import TestCase, mock
from bson.objectid import ObjectId
from restaurant.routes import update_order_status
from restaurant import app, db
from mongomock import MongoClient




class TestUpdateOrderStatus(TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.mock_db = MongoClient().db
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['MONGO_URI'] = ''
        app.config['MONGO_DBNAME'] = 'test_db'

    def test_update_order_status(self):
         with app.test_request_context(headers={'email': 'test@example.com'}):
            order_id = ObjectId()
            db['users'].insert_one({'email': 'test@example.com'})
            db['orders'].insert_one({'_id': order_id, 'status': 'Pending'})
            data = {'status': 'Delivered'}
            with app.test_client() as client:
                response = client.put(f'/api/v1/orders/update/{str(order_id)}', headers={'email': 'test@example.com'}, data=json.dumps(data), content_type='application/json')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.data), {'message': {'_id': str(order_id), 'status': 'Delivered'}})
                order = db.orders.find_one({'_id': order_id})
                self.assertEqual(order['status'], 'Delivered')

    def test_update_order_status_with_invalid_email(self):
        with app.test_request_context(headers={'email': 'invalid@example.com'}):
            order_id = ObjectId()
            db['orders'].insert_one({'_id': order_id, 'status': 'Pending'})
            data = {'status': 'Delivered'}
            with app.test_client() as client:
                response = client.put(f'/api/v1/orders/update/{str(order_id)}', headers={'email': 'invalid@example.com'}, data=json.dumps(data), content_type='application/json')
                self.assertEqual(response.status_code, 403)
                self.assertEqual(json.loads(response.data), {'error': 'Invalid email'})

    def test_update_order_status_with_invalid_order_id(self):
        with app.test_request_context(headers={'email': 'test@example.com'}):
            order_id = ObjectId()
            db['users'].insert_one({'email': 'test@example.com'})
            data = {'status': 'Delivered'}
            with app.test_client() as client:
                response = client.put(f'/api/v1/orders/update/{str(order_id)}', headers={'email': 'test@example.com'}, data=json.dumps(data), content_type='application/json')
                self.assertEqual(response.status_code, 404)
                self.assertEqual(json.loads(response.data), {'error': 'Order not found.'})

    def test_update_order_status_without_authorization(self):
        order_id = ObjectId()
        db['orders'].insert_one({'_id': order_id, 'status': 'Pending'})
        data = {'status': 'Delivered'}
        with app.test_client() as client:
            response = client.put(f'/api/v1/orders/update/{str(order_id)}',  data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 401)
            self.assertEqual(json.loads(response.data), {'message': 'Unauthorized access!'})

class TestBookHistoryApi(TestCase):

    def setUp(self):
        # Create a mock MongoClient instance and a mock database
        self.mock_db = MongoClient().db

        # Insert a mock user and order into the mock database
        self.mock_user = {'email': 'test@example.com', '_id': '1'}
        self.mock_order = {'user': '1', 'items': ['pizza', 'salad'], 'total': 25}
        self.mock_db.users.insert_one(self.mock_user)
        self.mock_db.orders.insert_one(self.mock_order)

        # Set the app configurations
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['MONGO_URI'] = ''
        app.config['MONGO_DBNAME'] = 'test_db'

        # Create a Flask test client
        self.app = app.test_client()

    def test_book_history_api(self):
        # Create a mock request with the user's email in the headers
        with app.test_request_context(headers={'email': 'test@example.com'}):
            headers = {'email': 'test@example.com'}
            response = self.app.get('/api/v1/bookHistory', headers=headers)
            data = response.get_json()
            # Assert that the response contains the correct order history
            self.assertEqual(data['success'], True)
            # self.assertEqual(len(data['result']), 1)
            # self.assertEqual(data['result'][0]['items'], ['pizza', 'salad'])
            # self.assertEqual(data['result'][0]['total'], 25)

class TestOrderHistoryApi(TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['MONGO_URI'] = ''
        app.config['MONGO_DBNAME'] = 'test_db'

    def test_order_history_api_with_valid_email(self):
        db['users'].insert_one({'email': 'test@example.com', '_id': ObjectId()})
        db['orders'].insert_many([
            {'user': str(ObjectId()), '_id': ObjectId(), 'status': 'Pending'},
            {'user': str(ObjectId()), '_id': ObjectId(), 'status': 'Delivered'}
        ])
        response = self.app.get('/api/v1/orderHistory', headers={'email': 'test@example.com'})
        self.assertEqual(response.status_code, 200)

    def test_order_history_api_with_invalid_email(self):
        response = self.app.get('/api/v1/orderHistory', headers={'email': 'invalid@example.com'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {'error': 'Invalid email'})

    def test_order_history_api_without_authorization(self):
        response = self.app.get('/api/v1/orderHistory')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {'message': 'Unauthorized access!'})
