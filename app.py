from flask import Flask, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request
from sklearn.preprocessing import OneHotEncoder
import pandas as pd
import pickle
import numpy as np
from sklearn.preprocessing import LabelEncoder

# Agroexpert code Start:
with open('model_pickle.pkl', 'rb') as file:
    model = pickle.load(file)
# Agroexpert code End:
    

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Agroexpert code STart:
def perform_encoding(df, columns, encoder=None):
    if encoder is None:
        encoder = OneHotEncoder(handle_unknown='ignore')
        encoder.fit(df[columns])
    encoded_data = pd.DataFrame(encoder.transform(df[columns]).toarray(), columns=encoder.get_feature_names_out(columns))
    return encoded_data, encoder
@app.route('/')
def hello_world():
     return render_template('home.html')

@app.route('/kolhapur')
def kolhapur():
    return render_template('kolhapur.html')

@app.route('/sangli')
def sangli():
    return render_template('sangli.html')

@app.route('/satare')
def satara():
    return render_template('satara.html')

@app.route('/pune')
def pune():
    return render_template('pune.html')

@app.route('/solapur')
def solapur():
    return render_template('solapur.html')

@app.route('/crop')
def crop():
    return render_template('crop.html')

@app.route('/prediction', methods=['POST','GET'])
def prediction():
    data = pd.read_csv('Crop and fertilizer dataset.csv')

    # Retrieve the form data
    district = request.form['District_Name']
    soil_color = request.form['soil_color']
    nitrogen = request.form['Nitrogen']
    phosphorus = request.form['Phosphorus']
    potassium = request.form['Potassium']
    pH = request.form['pH']
    rainfall = request.form['Rainfall']
    temperature = request.form['Temperature']

    # Create a dataframe from the form data
    input_categorical = pd.DataFrame({
        'District_Name': [district],
        'Soil_color': [soil_color],
    })
    input_numerical = pd.DataFrame({
        'Nitrogen': [nitrogen],
        'Phosphorus': [phosphorus],
        'Potassium': [potassium],
        'pH': [pH],
        'Rainfall': [rainfall],
        'Temperature': [temperature]
    })

    # Perform the necessary data encoding for the input data (similar to the code you provided)
    X_categorical = data[['District_Name', 'Soil_color']]
    X_numerical = data[['Nitrogen', 'Phosphorus', 'Potassium', 'pH', 'Rainfall', 'Temperature']]
    categorical_columns = ['District_Name', 'Soil_color']
    X_categorical_encoded, encoder = perform_encoding(X_categorical, categorical_columns)

    # encoder=OneHotEncoder(handle_unknown='ignore', sparse=False, sparse_output=False)
    input_categorical_encoded, _ = perform_encoding(input_categorical, categorical_columns, encoder)

    X_encoded = pd.concat([X_categorical_encoded, X_numerical], axis=1)
    input_encoded = pd.concat([input_categorical_encoded, input_numerical], axis=1)

    # Make predictions using the loaded model
    prediction = model.predict(input_encoded)
    link = data[(data['Crop'] == prediction[0][0]) & (data['Fertilizer'] == prediction[0][1])]['Link'].values[0]
    return render_template('result.html',prediction1=prediction[0][0],prediction2=prediction[0][1],plink=link)

# AgroExpert Code End

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'thisisasecretkey'



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))#change original to dashboard
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('crop.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('crop'))

    return render_template('register.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)