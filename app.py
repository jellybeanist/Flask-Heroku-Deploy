from bson import ObjectId
from flask import Flask, render_template, url_for, request, redirect, flash
from datetime import datetime
from werkzeug.utils import secure_filename
import array as arr
import os
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, request, render_template, \
    jsonify, g, session, redirect, make_response
import pymongo
import ssl

PATH = os.getcwd()

cluster = pymongo.MongoClient("mongodb+srv://e2649655:se560@cluster0.x3gv569.mongodb.net/?retryWrites=true&w=majority",
                              ssl_cert_reqs=ssl.CERT_NONE)

db = cluster["demo2"]
user_collection = db["Users"]
medicine_collection = db["Medicines"]
order_collection = db["Orders"]

app = Flask(__name__)


class Medicine:
    def __init__(self, medicine_name, manufacturer, category, active_ingredient, extra_dosage_info, dosage_info, id):
        self.medicine_name = medicine_name
        self.manufacturer = manufacturer
        self.category = category
        self.active_ingredient = active_ingredient
        self.extra_dosage_info = extra_dosage_info
        self.dosage_info = dosage_info
        self._id = id

    subTotal = 0
    curAmount = 0

    def __repr__(self):
        return '<Medicine %r>' % self.medicine_name


class User:
    def __init__(self, name, user_name, e_mail, password, id):
        self.name = name
        self.user_name = user_name
        self.e_mail = e_mail
        self.password = password
        self._id = id

    def __repr__(self):
        return '<User %r>' % self.user_name


class Order:
    def __init__(self, name, email, address, medicine, amount, user_id, id):
        self.name = name
        self.email = email
        self.address = address
        self.medicine = medicine
        self.amount = amount
        self.user_id = user_id
        self._id = id

    def __repr__(self):
        return '<Order %r>' % self.name


@app.route('/<user_id>/userPage/', methods=['POST', 'GET'])
def userPage(user_id):
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])

    return render_template('userPage.html', user=user_obj)


@app.route('/lastOrders/<user_id>/', methods=['POST', 'GET'])
def lastOrders(user_id):
    orders = order_collection.find({"user_id": ObjectId(user_id)})
    order_list = []

    for order in orders:
        order_to_add = Order(order["name"], order["email"], order["address"], order["medicine_name"], order["amount"],
                             order["user_id"], order["_id"])
        order_list.append(order_to_add)

    user = user_collection.find_one({"_id": ObjectId(user_id)})
    user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])

    return render_template('lastOrders.html', orders=order_list, user=user_obj)


@app.route('/<user_id>/', methods=['POST', 'GET'])
def index_user(user_id):
    global carts

    medicines = medicine_collection.find()
    user = user_collection.find_one({"_id": ObjectId(user_id)})

    cart = carts[user["_id"]]

    medicine_list = []
    for medicine in medicines:
        if medicine["extra_dosage_info"] == "yes":
            med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                           medicine["category"], medicine["active_ingredient"],
                           medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
            medicine_list.append(med)
        else:
            med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                           medicine["category"], medicine["active_ingredient"],
                           medicine["extra_dosage_info"], "", medicine["_id"])
            medicine_list.append(med)

    return render_template('indexUser.html', medicinesCart=cart, medicines=medicine_list, user=user)


@app.route('/admin', methods=['POST', 'GET'])
def index_admin():
    if request.method == 'POST':
        medicine_medicine_name = request.form['medicine_name']
        medicine_manufacturer = request.form['manufacturer']
        medicine_category = request.form['category']
        medicine_active_ingredient = request.form['active_ingredient']
        medicine_extra_dosage_info = request.form['extra_dosage_info']
        medicine_dosage_info = request.form['dosage_info']

        if medicine_extra_dosage_info == "yes":
            medicine_collection.insert_one(
                {"medicine_name": medicine_medicine_name,
                 "manufacturer": medicine_manufacturer,
                 "category": medicine_category, "active_ingredient": medicine_active_ingredient,
                 "extra_dosage_info": medicine_extra_dosage_info, "dosage_info": medicine_dosage_info})
        else:
            medicine_collection.insert_one(
                {"medicine_name": medicine_medicine_name,
                 "manufacturer": medicine_manufacturer,
                 "category": medicine_category, "active_ingredient": medicine_active_ingredient,
                 "extra_dosage_info": medicine_extra_dosage_info})

        return redirect('/admin')
    else:

        medicines = medicine_collection.find()

        medicine_list = []

        for medicine in medicines:
            if medicine["extra_dosage_info"] == "yes":
                med = Medicine(medicine["medicine_name"], medicine["manufacturer"], medicine["category"],
                               medicine["active_ingredient"],
                               medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
                medicine_list.append(med)
            else:
                med = Medicine(medicine["medicine_name"], medicine["manufacturer"], medicine["category"],
                               medicine["active_ingredient"],
                               medicine["extra_dosage_info"], "", medicine["_id"])
                medicine_list.append(med)

        return render_template('indexAdmin.html', medicines=medicine_list)


@app.route('/delete/<medicine_id>')
def delete(medicine_id):
    medicine_collection.delete_one({"_id": ObjectId(medicine_id)})
    return redirect('/admin')


@app.route('/<user_id>/add/<medicine_id>')
def add(user_id, medicine_id):
    global carts

    user = user_collection.find_one({"_id": ObjectId(user_id)})
    medicine = medicine_collection.find_one({"_id": ObjectId(medicine_id)})

    medicine_to_add = Medicine(medicine["medicine_name"], medicine["manufacturer"], medicine["category"],
                               medicine["active_ingredient"],
                               medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
    cart = carts[user["_id"]]
    control = 1

    if (len(cart) > 0):
        for medicine in cart:
            if (medicine._id == ObjectId(medicine_id)):
                medicine.curAmount = medicine.curAmount + 1
                control = 0
                break
        if (control == 1):
            medicine_to_add.curAmount = medicine_to_add.curAmount + 1
            cart.append(medicine_to_add)
    elif (len(cart) == 0):
        medicine_to_add.curAmount = medicine_to_add.curAmount + 1
        cart.append(medicine_to_add)

    return index_user(user["_id"])


@app.route('/<user_id>/remove/<medicine_id>')
def remove(user_id, medicine_id):
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])

    medicines = medicine_collection.find()
    medicine_list = []
    for medicine in medicines:
        if medicine["extra_dosage_info"] == "yes":
            med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                           medicine["category"], medicine["active_ingredient"],
                           medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
            medicine_list.append(med)
        else:
            med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                           medicine["category"], medicine["active_ingredient"],
                           medicine["extra_dosage_info"], "", medicine["_id"])
            medicine_list.append(med)

    global carts

    cart = carts[user["_id"]]

    if (len(cart) > 0):
        for medicine in cart:
            if (medicine._id == ObjectId(medicine_id)):
                if medicine.curAmount > 1:
                    medicine.curAmount = medicine.curAmount - 1
                else:
                    medicine.curAmount = 0
                    cart.remove(medicine)
                break

    return render_template('indexUser.html', medicinesCart=cart, medicines=medicine_list, user=user_obj)


@app.route('/update/<medicine_id>', methods=['GET', 'POST'])
def update(medicine_id):
    if request.method == 'POST':
        medicine_medicine_name = request.form['medicine_name']
        medicine_manufacturer = request.form['manufacturer']
        medicine_category = request.form['category']
        medicine_active_ingredient = request.form['active_ingredient']
        medicine_extra_dosage_info = request.form['extra_dosage_info']
        medicine_dosage_info = request.form['dosage_info']

        filter = {"_id": ObjectId(medicine_id)}
        if medicine_extra_dosage_info == "yes":
            newvalues = {"$set": {'medicine_name': medicine_medicine_name, "manufacturer": medicine_manufacturer,
                                  "category": medicine_category,
                                  "active_ingredient": medicine_active_ingredient,
                                  "extra_dosage_info": medicine_extra_dosage_info, "dosage_info": medicine_dosage_info}}
        else:
            newvalues = {"$set": {'medicine_name': medicine_medicine_name, "manufacturer": medicine_manufacturer,
                                  "category": medicine_category,
                                  "active_ingredient": medicine_active_ingredient,
                                  "extra_dosage_info": medicine_extra_dosage_info}}
        medicine_collection.update_one(filter, newvalues)

        return redirect('/admin')


    else:

        medicine = medicine_collection.find_one({"_id": ObjectId(medicine_id)})
        if medicine["extra_dosage_info"] == "yes":
            med = Medicine(medicine["medicine_name"], medicine["manufacturer"], medicine["category"],
                           medicine["active_ingredient"],
                           medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
        else:
            med = Medicine(medicine["medicine_name"], medicine["manufacturer"], medicine["category"],
                           medicine["active_ingredient"],
                           medicine["extra_dosage_info"], "", medicine["_id"])

        return render_template('update.html', medicine=med)


@app.route('/updateUser/<user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    user = user_collection.find_one({"_id": ObjectId(user_id)})

    if request.method == 'POST':
        user_name = request.form['name']
        user_username = request.form['username']
        user_email = request.form['email']
        user_password = request.form['password']

        filter = {"_id": ObjectId(user_id)}
        newvalues = {"$set": {'name': user_name, "user_name": user_username, "e_mail": user_email,
                              "password": user_password}}

        user_collection.update_one(filter, newvalues)

        return index_user(user_id)

    else:
        user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])
        return render_template('userSettings.html', user=user_obj)


@app.route('/<user_id>/order', methods=['GET'])
def order(user_id):
    done = 0

    global carts

    user = user_collection.find_one({"_id": ObjectId(user_id)})
    user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])

    cart = carts[user["_id"]]

    total = 0

    return render_template('Order Page.html', medicines=cart, user=user_obj, done=done)


@app.route('/<user_id>/order', methods=['POST'])
def order_done(user_id):
    done = 1
    global carts

    order_name = request.form['name']
    order_address = request.form['address']
    order_email = request.form['email']

    user = user_collection.find_one({"_id": ObjectId(user_id)})
    user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])
    cart = carts[user["_id"]]

    for medicine in cart:
        order_collection.insert_one(
            {"user_id": user["_id"], "name": order_name, "address": order_address, "email": order_email,
             "medicine_name": medicine.medicine_name, "amount": medicine.curAmount})

    carts[user["_id"]] = []

    return render_template('Order Page.html', medicines=cart, user=user_obj, done=done)


@app.route('/<user_id>/search', methods=['GET', 'POST'])
def search_results(user_id):
    if request.method == 'POST':
        search_string = request.form['search']

        global carts

        if (search_string == ""):

            medicines = medicine_collection.find()

            medicine_list = []
            for medicine in medicines:
                if medicine["extra_dosage_info"] == "yes":
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
                    medicine_list.append(med)
                else:
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], "", medicine["_id"])
                    medicine_list.append(med)

            user = user_collection.find_one({"_id": ObjectId(user_id)})
            user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])
            cart = carts[user["_id"]]
            return render_template('indexUser.html', medicinesCart=cart, medicines=medicine_list, user=user_obj)
        else:

            medicines = medicine_collection.find({"medicine_name": search_string})

            medicine_list = []
            for medicine in medicines:
                if medicine["extra_dosage_info"] == "yes":
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
                    medicine_list.append(med)
                else:
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], "", medicine["_id"])
                    medicine_list.append(med)

            user = user_collection.find_one({"_id": ObjectId(user_id)})
            user_obj = User(user["name"], user["user_name"], user["e_mail"], user["password"], user["_id"])
            cart = carts[user["_id"]]

            return render_template('indexUser.html', medicinesCart=cart, medicines=medicine_list, user=user_obj)


@app.route('/searchAdmin', methods=['GET', 'POST'])
def search_results_admin():
    if request.method == 'POST':
        search_string = request.form['search']

        if (search_string == ""):

            medicines = medicine_collection.find()

            medicine_list = []
            for medicine in medicines:
                if medicine["extra_dosage_info"] == "yes":
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
                    medicine_list.append(med)
                else:
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], "", medicine["_id"])
                    medicine_list.append(med)

            return render_template('indexAdmin.html', medicines=medicine_list)
        else:
            medicines = medicine_collection.find({"medicine_name": search_string})

            medicine_list = []
            for medicine in medicines:
                if medicine["extra_dosage_info"] == "yes":
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], medicine["dosage_info"], medicine["_id"])
                    medicine_list.append(med)
                else:
                    med = Medicine(medicine["medicine_name"], medicine["manufacturer"],
                                   medicine["category"], medicine["active_ingredient"],
                                   medicine["extra_dosage_info"], "", medicine["_id"])
                    medicine_list.append(med)

            return render_template('indexAdmin.html', medicines=medicine_list)


# Set the route and accepted methods
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('Login.html')


@app.route('/register', methods=['GET'])
def register_page():
    return render_template('Register.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data['username']
    password = data['password']
    user = user_collection.find_one({"user_name": username})

    if not user:
        return make_response('User not found', 401)
    if password == user["password"]:
        return index_user(user["_id"])
    else:
        return make_response('Password is incorrect', 401)


# endpoint to create new user
@app.route('/signup', methods=['POST'])
def add_user():
    global carts

    cart = []

    data = request.form
    username = data['username']
    email = data['email']
    password = data['password']
    name = data['name']

    user = user_collection.insert_one({"name": name, "user_name": username,
                                       "e_mail": email, "password": password})

    carts[user.inserted_id] = cart

    return redirect('/login')


if __name__ == "__main__":

    users = user_collection.find()
    carts = {}

    for user in users:
        username = user["_id"]
        carts[username] = []

    app.run(debug=True)
