
# app.py
from flask import Flask, render_template,request,redirect,url_for,flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from jinja2 import Template


app = Flask(__name__,static_folder='static',template_folder='templates')
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY']='thisismylittlesecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:SDEEP%402003@localhost/e_way'
db = SQLAlchemy(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    # fetch the user from db using email
    dbuser = Users.query.filter_by(user_id=user_id).first()

    user=User()
    user.id=dbuser.user_id
    user.role=dbuser.role
    return user


class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True,nullable=False,autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(80), nullable=False,default='user')

    def _repr_(self):
        return '<User %r>' % self.username


class Company(db.Model):
    comp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comp_name = db.Column(db.String(20), unique=True, nullable=False)
    comp_hq = db.Column(db.String(20))
    comp_head = db.Column(db.String(30))
    no_of_emp = db.Column(db.BigInteger)
    models = db.Column(db.Integer)

class Vehicles(db.Model):
    v_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comp_id = db.Column(db.Integer, db.ForeignKey('Company.comp_id', ondelete='CASCADE'), nullable=False)
    v_name = db.Column(db.String(20))
    max_range = db.Column(db.Integer)
    cost = db.Column(db.BigInteger)
    max_speed = db.Column(db.Integer)
    station_id = db.Column(db.Integer, db.ForeignKey('Station.station_id', ondelete='CASCADE'))

class Cost(db.Model):
    v_id = db.Column(db.Integer, primary_key=True)
    v_name = db.Column(db.String(50))
    battery = db.Column(db.Float(9, 2))
    rd = db.Column(db.Float(9, 2))
    body = db.Column(db.Float(9, 2))
    subsidy = db.Column(db.Float(9, 2))
    total = db.Column(db.Float(9, 2))

class Station(db.Model):
    station_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comp_id = db.Column(db.Integer, db.ForeignKey('Company.comp_id', ondelete='CASCADE'), nullable=False)
    location = db.Column(db.String(20))
    no_of_units = db.Column(db.BigInteger)
    cost = db.Column(db.Float(9, 2))
    max_limit = db.Column(db.Integer)

class Service(db.Model):
    comp_id = db.Column(db.Integer, db.ForeignKey('Company.comp_id', ondelete='CASCADE'), primary_key=True)
    v_id = db.Column(db.Integer, db.ForeignKey('Vehicles.v_id', ondelete='CASCADE'), primary_key=True)
    total_complaints = db.Column(db.Integer)
    total_comp_solved = db.Column(db.Integer)
    ratings = db.Column(db.Integer)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # check the user from db with email and password

        email=str(request.form.get('email'))
        password=str(request.form.get('password'))
        print(email,password)
        dbuser = Users.query.filter_by(email=email,password=password).first()

        if dbuser:
            user = User()
            user.id = dbuser.user_id
            user.role = dbuser.role
            login_user(user)
            return redirect(url_for('company'))
        else:
            return 'Invalid email or password'
    
    return render_template('login.html')

# use same format for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # check the user from db with email and password
        try:
            name = str(request.form.get('name'))
            email = str(request.form.get('email'))
            password = str(request.form.get('password'))
            dbuser = Users(name=name, email=email, password=password)
            db.session.add(dbuser)
            db.session.commit()

            # login the user using same format
            user = User()
            user.id = dbuser.user_id
            user.role = dbuser.role
            login_user(user)

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Error: %s' % (str(e)))
        except Exception as e:
            flash('Error: %s' % (str(e)))
        return redirect(url_for('company'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Logged out'

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/company')
def company():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    # fetch all companies from db
    companies = Company.query.all()
    return render_template('company.html', companies=companies)

@app.route('/company/create', methods=['GET', 'POST'])
def company_create():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if current_user.role != 'admin':
        return 'You are not authorized to create company'
    if request.method == 'POST':
        comp_name = str(request.form.get('comp_name'))
        comp_hq = str(request.form.get('comp_hq'))
        comp_head = str(request.form.get('comp_head'))
        no_of_emp = int(request.form.get('no_of_emp'))
        models = int(request.form.get('models'))

        company = Company(comp_name=comp_name, comp_hq=comp_hq, comp_head=comp_head, no_of_emp=no_of_emp, models=models)
        db.session.add(company)
        db.session.commit()
        return redirect(url_for('company'))

    return render_template('create-company.html')

@app.route('/company/edit/<int:comp_id>', methods=['GET', 'POST'])
def company_edit(comp_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if current_user.role != 'admin':
        return 'You are not authorized to edit company'
    if request.method == 'POST':
        comp_name = str(request.form.get('comp_name'))
        comp_hq = str(request.form.get('comp_hq'))
        comp_head = str(request.form.get('comp_head'))
        no_of_emp = int(request.form.get('no_of_emp'))
        models = int(request.form.get('models'))

        company = Company.query.get(comp_id)
        company.comp_name = comp_name
        company.comp_hq = comp_hq
        company.comp_head = comp_head
        company.no_of_emp = no_of_emp
        company.models = models
        db.session.commit()
        return redirect(url_for('company'))

    company = Company.query.get(comp_id)
    return render_template('update-comp.html', company=company)

@app.route('/company/delete/<int:comp_id>', methods=['GET', 'POST'])
def company_delete(comp_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if current_user.role != 'admin':
        return 'You are not authorized to delete company'
    if request.method == 'POST':
        company = Company.query.get(comp_id)
        db.session.delete(company)
        db.session.commit()
        return redirect(url_for('company'))
    
    company = Company.query.get(comp_id)
    return render_template('delete-comp.html', company=company)


@app.route('/vehicle/<int:comp_id>')
def vehicle(comp_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    print(comp_id)
    # fetch vehicles based on company id
    sql = text("SELECT * FROM vehicles WHERE comp_id = :comp_id")
    vehicles = db.session.execute(sql, {'comp_id': comp_id})       
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/station/<int:comp_id>')
def station(comp_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    sql = text("SELECT * FROM station WHERE comp_id = :comp_id")
    stations = db.session.execute(sql, {'comp_id': comp_id})   
    return render_template('station.html', stations=stations)

@app.route('/service/<int:comp_id>')
def service(comp_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    services = Service.query.filter_by(comp_id=comp_id)
    return render_template('service.html', services=services)

@app.route('/cost/<int:v_id>')
def cost(v_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    cost = Cost.query.filter_by(v_id=v_id).first()
    if cost:
        formatted_cost = {
            'v_id': cost.v_id,
            'v_name': cost.v_name,
            'battery':"{:.2f}".format(cost.battery) ,
            'rd': "{:.2f}".format(cost.rd),
            'body': "{:.2f}".format(cost.body),
            'subsidy': "{:.2f}".format(cost.subsidy),
            'total': "{:.2f}".format(cost.total)
        }
        return render_template('cost.html', cost=formatted_cost)
    else:
        return render_template('cost.html', cost=None)
    
@app.route('/cost/edit/<int:v_id>', methods=['GET', 'POST'])
def cost_edit(v_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if current_user.role != 'admin':
        return 'You are not authorized to edit cost'
    if request.method == 'POST':
        battery = float(request.form.get('battery'))
        rd = float(request.form.get('rd'))
        body = float(request.form.get('body'))
        subsidy = float(request.form.get('subsidy'))
        total = battery + rd + body - subsidy

        cost = Cost.query.get(v_id)
        cost.battery = battery
        cost.rd = rd
        cost.body = body
        cost.subsidy = subsidy
        cost.total = total
        db.session.commit()
        
        
        return redirect(url_for('cost', v_id=v_id))

    cost = Cost.query.get(v_id)
    return render_template('update-cost.html', cost=cost)

@app.route('/cost/delete/<int:v_id>')
def cost_delete(v_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if current_user.role != 'admin':
        return 'You are not authorized to delete cost'
    cost = Cost.query.get(v_id)
    db.session.delete(cost)
    db.session.commit()
    return redirect(url_for('company'))


if __name__ == '__main__':
    app.run(debug=True)