__author__ = 'Stuart'

from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask.ext.login import UserMixin, AnonymousUserMixin
from sqlalchemy.dialects.postgresql import JSONB
import hashlib
from datetime import datetime
# multiprocessing
import stripe

class Permission:
    CREATE = 0x01  # can create Q's and A's, and edit own
    COMMENT = 0x02  # write posts or comments, edit same posts and comments
    WRITE_ARTICLES = 0x04  # for blog - includes edit powers
    EDIT = 0x08  # edit everything
    ADMINISTER = 0x80

class Role(db.Model):
    """
    default should be set to True for only one role, False for others. Role marked as default will be assigned upon
    registration.
    Permissions is integer used as bit flags. Each task will be assigned a bit position, and for each role the tasks
    that are allowed for that role will have their bits set to 1.
    """
    __tablename__ = 'roles'  # SQLA doesn't use the plural naming convention so, explicitly name it
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64),unique=True)
    default = db.Column(db.Boolean, default=False, index=True)  # default should be true for only one Role, false else
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    # lists users assoc with role. backref adds role attr to User. lazy=dynamic returns query that hasn't been exec'd
    # yet so filters can be added to is.

    def __repr__(self):
        return '<Role {}>'.format(self.name)

    @staticmethod
    def insert_roles():
        """
        Tries to find existing roles by name and update those. New role obj created only for role names not in db
        already. This done so that role list can be updated in future when changes need to be made. To add a new role or
        change the permission assignments for a role, change the roles dictionary and return the function.
        Anonymous role doesn't need to be represented in db, as it is designed for users who aren't in the db.
        To apply to db: shell, Role.insert_roles() Role.query.all()

        This doesn't add roles to users. Merely permissions get attached to roles in the roles db.

        Fucking remember to do this before inserting users. Dumbass. Otherwise create one that inserts default perms
        for all later users. Dumbass. It's easy, if user.role == None, role=default. Shithead.
        :return:
        """
        roles = {'User': (Permission.CREATE | Permission.COMMENT, True),
                 'Moderator': (Permission.CREATE | Permission.COMMENT |
                               Permission.WRITE_ARTICLES | Permission.EDIT, False),
                 'Administrator': (0xff, False)}  # can change these and run it later to change permissions
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)  # create new role
            role.permissions = roles[r][0]  # set role's permissions
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

class User(db.Model, UserMixin):
    """
    To-Do: change password like here: https://www.reddit.com/r/technology/comments/3ennbw/websites_please_stop_blocking_password_managers/
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)  ############CHANGE THIS LATER################# FUCK EMAIL CONFIRM
    name = db.Column(db.String(128))  # Split into first and last
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)  # make sure it's a callable at end
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    created_qs = db.relationship('Question', backref='creator', lazy='dynamic')
    created_as = db.relationship('Answer', backref='author', lazy='dynamic')
    stripe = db.Column(JSONB)
    earned = db.Column(db.Float, default=0.0)
    #banked = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def __init__(self, **kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['TIP_ADMIN']:  # at first registration, checks to see if email is
                # the admin's email and assigns them admin powers
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if current_app.config['TIP_AUTO_APPROVE']:
            self.visible = True
        if self.stripe is None:
            pass #TODO: enable stripe shit
            # self.set_stripe_customer()

    ##### UTILITY #######

    def can(self, permissions):
        """
        performs bitwise & operation between permissions and permissions of assigned role. Returns True if all the
        requested bits are present in the role, which means user should be allowed to perform the tasks.
        00000001 & 00000010 = 000000011
        :param permissions:
        :return:
        """
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def has_answered(self,id):
        question_id = id
        answered = self.created_as.filter_by(question_id=question_id).all()
        return len(answered)

    def earned_pretty(self):
        if self.earned != 0:
            earned = str(self.earned)
            earned = "$" + earned[:-2] + "." + earned[:-2]
            return earned
        else:
            return "Nothing yet"

    def date_pretty(self):
        return self.member_since.strftime("%B %Y")

    ###### Registration / authentication related #########

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        db.session.commit()
        return True

    def ping(self):
        """
        must be called each time a request from user is rec'd. Since the before_app_request handler in auth
        blueprint runs before every request, it can do this easily.
        :return:
        """
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    @property
    def password(self):
        """
        Trying to read password property will return this error, since original password can't be
        recovered once hashed
        :return:
        """
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        When password property is set, setter method will hash it and write it to the password_hash
        field
        :param password:
        :return:
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        """
        Takes pw and checks it for verification against hashed version stored in User model.
        If returns True, then password is corect.
        :param password:
        :return:
        """
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):  # generates token with default validity 1 hr
        """
        Generates encrypted confirmation token based on a cryptokey (SECRET_KEY here) containing confirmation ID for
        account.
        Secured cookies signed by its dangerous can be used for this token purpose.
        Dumps takes given data ({confirm:self.id}) and generates crypto token in the form of a long-ass random
        string
        :param expiration:
        :return:
        """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)  # creates JSON web sign with exp time
        return s.dumps({'confirm':self.id})  #

    def confirm(self, token):
        """
        Serializer loads() method takes token
        :param token:
        :return:
        """
        s = Serializer(current_app.config['SECRET_KEY'])  # generates thingy
        try:
            data = s.loads(token)  # tries to load based off of token, checks token time too
        except:
            return False  # oh no! .loads threw an exception for invalid token or invalid time, so we return False
        if data.get('confirm') != self.id:  # if token not for current_user.id, deny access.
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True


    ############ STRIPE RELATED ###########

    def set_stripe_customer(self):
        """
        creates strip customer object (JSON), looks like this
        {
          "account_balance": 0,
          "created": 1453259107,
          "currency": null,
          "default_source": null,
          "delinquent": false,
          "description": null,
          "discount": null,
          "email": "jimmy@wales.com",
          "id": "cus_7khgbodYrVgmWj",
          "livemode": false,
          "metadata": {
            "username": "jimmy"
          },
          "object": "customer",
          "shipping": null,
          "sources": {
            "data": [],
            "has_more": false,
            "object": "list",
            "total_count": 0,
            "url": "/v1/customers/cus_7khgbodYrVgmWj/sources"
          },
          "subscriptions": {
            "data": [],
            "has_more": false,
            "object": "list",
            "total_count": 0,
            "url": "/v1/customers/cus_7khgbodYrVgmWj/subscriptions"
          }
        }

        http://stackoverflow.com/questions/23878070/using-json-type-with-flask-sqlalchemy-postgresql
        http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#sqlalchemy.dialects.postgresql.JSONB

        TODO: Make this Async
        :return:
        """
        # why is this shutting server down after?
        # put it in a server queue
        # try:
        cust = stripe.Customer.create(
            metadata={
                "user_id":self.id,
                "username":self.username
            },
            email=self.email
        )
        self.stripe = cust

        db.session.add(self)
        db.session.commit()
        # except stripe.error.APIConnectionError as e:
        #     print("connection error")
        #     return e
        # except stripe.error.AuthenticationError as e:
        #     print("API key needed")
        #     return e
        # except stripe.error.StripeError as e:
        #     print("some other error")
        #     return e

    def get_stripe_customer(self):
        print(self.stripe['id'])
        # return stripe.Customer.retrieve(self.stripe_id)

    def update_stripe_customer(self):
        pass

    ####### Testing related ##########
    @staticmethod
    def create_fakes(count=10):
        # http://www.joke2k.net/faker/
        from faker import Factory

        faker=Factory.create()

        for i in range(count):
            u = User(email=faker.safe_email(),
                     username=faker.user_name(),
                     password="password",
                     confirmed=True,
                     name=faker.name(),
                     )
            db.session.add(u)
            db.session.commit()

class AnonymousUser(AnonymousUserMixin):
    """
    registered to anonymous users when user isn't logged in. App can thus still freely call .can() and .is_admin()
    without checking if is logged in first.
    """
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False
login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True)
    description = db.Column(db.Text)
    visible = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # one to many
    # creator
    current_value = db.Column(db.Integer, default=0, index=True)
    date = db.Column(db.DateTime(),default=datetime.utcnow, index=True)
    category = db.Column(db.String(64),index=True)
    solved = db.Column(db.Boolean, default=False, index=True)
    solved_date = db.Column(db.DateTime(), index=True)
    answers = db.relationship('Answer',backref="question",lazy='dynamic',
                              primaryjoin="Question.id==Answer.question_id")
    accepted_id = db.Column(db.Integer, db.ForeignKey("answers.id"))
    # accepted_answer = db.relationship('Answer',backref="answered_q",lazy='dynamic', uselist=False,
    #                                   primaryjoin="Question.accepted_id==Answer.id") #
    # or answers.filter_by(accepted)
    # http://stackoverflow.com/questions/3464443/sqlalchemy-one-to-one-relationship-with-declarative
    # http://docs.sqlalchemy.org/en/rel_0_7/orm/relationships.html#relationship-primaryjoin

    def __repr__(self):
        return "id: {}, title: {}".format(self.id,self.title)

    def total_up(self):
        total = 0
        for contribution in self.contributions:
            total += contribution.amount
        self.current_value = total
        db.session.add(self)
        db.session.commit()

    def toggle_visibility(self):
        self.visible = not self.visible
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def create_fakes(count=3):
        from faker import Factory
        import random

        faker=Factory.create()

        users = User.query.all()
        for u in users:
            q = Question(title=faker.bs(),
                     description=faker.catch_phrase(),
                     visible=True,
                     creator= u,
                     category=random.choice(current_app.config["CATEGORIES"]),
                     )
            db.session.add(q)
            db.session.commit()

class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(),default=datetime.utcnow, index=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # one to many
    # author
    question_id = db.Column(db.Integer,db.ForeignKey("questions.id"))
    # question
    content = db.Column(db.Text)
    accepted = db.Column(db.Boolean, default=False)  # has it been accepted?
    # answered_q

    def __repr__(self):
        return "answer: {}, content: {}".format(self.id, self.content)

    @staticmethod
    def create_fakes(count=3):
        from faker import Factory
        import random

        faker = Factory.create()

        questions = Question.query.all()
        users = User.query.all()
        for q in questions:
            for i in range(count):
                a = Answer(author = random.choice(users),
                           question = q,
                           content = faker.bs(),
                           )
                db.session.add(a)
                db.session.commit()

    def accept(self):
        # https://www.reddit.com/r/flask/comments/2o4ejl/af_flask_sqlalchemy_two_foreign_keys_referencing/
        # http://stackoverflow.com/questions/22355890/sqlalchemy-multiple-foreign-keys-to-the-same-primary-id-in-another-table
        # http://stackoverflow.com/questions/16976967/sqlalchemy-multiple-foreign-keys-to-same-table
        # http://stackoverflow.com/questions/19606745/flask-sqlalchemy-error-typeerror-incompatible-collection-type-model-is-not
        # http://stackoverflow.com/questions/28280507/setup-relationship-one-to-one-in-flask-sqlalchemy
        # https://www.reddit.com/r/flask/comments/45p49u/af_flask_sqlalchemy_relationships_how_to_refer_to/
        try:
            self.accepted=True
            self.question.solved = True
            self.question.accepted_id = self.id
            self.question.solved_date = datetime.utcnow()
            db.session.add(self)
            db.session.add(self.question)
            db.session.commit()
            return "success"
        except Exception as e:
            return e

