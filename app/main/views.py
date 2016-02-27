from flask import render_template, redirect, request, url_for, flash, current_app, session, jsonify
from flask.ext.login import current_user, login_required
from . import main
from .forms import CreateQuestionForm, EditQuestionForm, ReportForm, CreateAnswerForm, EditAnswerForm, AcceptAnswerForm
from .. import db
from ..models import User, Question, Answer, Permission
from ..email import send_grid_email
from .. decorators import admin_required
from datetime import datetime


@main.route('/')
def index():
    # http://stackoverflow.com/questions/9861990/sqlalchemy-how-to-order-query-results-order-by-on-a-relationships-field
    #todo: pagination object, categories, sideways scrolling,
    #todo: make it look like this http://foundation.zurb.com/apps/resources.html

    top = Question.query.order_by(Question.current_value.desc()).limit(10).all() # Top pots by value
    recent = Question.query.order_by(Question.date.desc()).limit(10).all() # sort by time, use timedelta?
    completed = Question.query.filter_by(solved=True).order_by(Question.solved_date.desc()).limit(6).all() # most recently completed
    return render_template("index.html", top=top, recent=recent, completed=completed)


@main.route('/profile/<username>/')
def profile(username):
    """
    Public profile, with posted questions, answers, and maybe $ earned.
    Questions and answers should all be together in one "feed" but different colors. Have a filter for Q's and A's.
    :param id:
    :return:
    """
    user = User.query.filter_by(username=username).first()
    questions = Question.query.filter_by(creator_id=user.id).all()
    answers = Answer.query.filter_by(creator_id=user.id).all()
    return render_template('profile.html', user=user, questions=questions, answers=answers)

@main.route('/profile/<username>/edit/')
@login_required
def profile_edit(username):
    """
    edit profile. As of now, not needed. When we get more deeeeeetails later
    :param username:
    :return:
    """
    # form = EditProfileForm
    return render_template('profile_edit.html')


@main.route('/questions/<int:id>/', methods=['POST', 'GET'])
def question(id):
    """
    Shows question description etc, and maybe also creator info.
    Also has answer question form
    Todo: Delete button. Should it be a simple button with a POST and refresh, or should it be a form?
    :param id:
    :return:
    """
    form = CreateAnswerForm()
    question = Question.query.get_or_404(id)  # get gets things based on primary key, otherwise use .filter_by
    if form.validate_on_submit() and current_user.can(Permission.CREATE):
        # Add answer
        answer = Answer(author=current_user._get_current_object(), question=question, content=form.answer.data)
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('main.question', id=id))
    elif form.validate_on_submit() and current_app.has_answered(id=id):
        # just in case
        flash("Sorry, you can't answer a question more than once")
        return redirect(url_for('main.question', id=id))
    elif not question.visible and not current_user.is_administrator():
        # just in case
        flash("That page isn't ready for the public yet, sorry!")
        return redirect(url_for("main.index"))
    else:
        creator = User.query.filter_by(id=question.creator_id).first()
        if question.solved:
            accepted = Answer.query.get_or_404(question.accepted_id)
        else:
            accepted = None
        # some way to find if a user has already answered the question
        return render_template("question.html", creator=creator, id=id, form=form, Permission=Permission,
                               question=question, a=accepted)


@main.route('/ask/', methods=['POST','GET'])
@login_required
def ask():
    """
    create question
    :return:
    """
    #todo add more categories
    form = CreateQuestionForm()
    if form.validate_on_submit() and current_user.can(Permission.CREATE):
        title = form.title.data
        desc = form.description.data
        category = form.category.data
        # if Question.query.filter_by(title=form.title.data).first():
        #     flash("Sorry, there's already a question by that name. How about you pick another one?")
        #     print("exists")
        #     return render_template("question_create.html", form=form)  # save data in session and pre-fill form. Also sanitize.
        # else:
        q = Question(title=title, description=desc, creator=current_user._get_current_object(), category=category)
        db.session.add(q)
        db.session.commit()
        return redirect(url_for('main.question_created', id=q.id))
    else:
        return render_template("question_create.html", form=form)


@main.route('/questions/<int:id>/created/')
@login_required
def question_created(id):
    """
    confirms it is created, adds a link to the question,
    has text prompting user to add a prize
    :param id:
    :return:
    """
    # q = Question.query.get_or_404(id)
    return render_template("question_conf.html", id=id)


@main.route('/questions/<int:id>/reward/')
@login_required
def add_reward(id):
    """
    DO AFTER CHECKING CREATION OF SHIT
    :param id:
    :return:
    """
    q = Question.query.get_or_404(id)
    creator = User.query.filter_by(id=q.creator_id).first()
    return render_template("question_add_reward.html", q=q, creator=creator)


@main.route('/questions/<int:id>/edit/', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    """
    Edit question, add links to resources.
    :param id:
    :return:
    """
    question = Question.query.get_or_404(id) # todo: prefill
    form = EditQuestionForm()
    if form.validate_on_submit():
        question.description = form.description.data
        question.category = form.category.data
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('main.question', id=id))
    return render_template("question_edit.html", question=question, form=form)

@main.route('/questions/<int:id>/answers/<int:aid>/edit/', methods=['GET','POST'])
@login_required
def edit_answer(id, aid):
    # todo: prefill
    q = Question.query.get_or_404(id)
    a = Answer.query.get_or_404(aid)
    if q.solved:
        flash("That's already been solved, you can't edit that anymore.")
        return redirect(url_for('main.question', id=id))
    form = EditAnswerForm()
    if form.validate_on_submit():
        a.content = form.answer.data
        db.session.add(a)
        db.session.commit()
        flash("Question updated.")
        return redirect(url_for('main.question', id=id))
    else:
        return render_template('answer_edit.html', q=q, a=a, form=form)

@main.route('/questions/<int:id>/accept/<int:aid>/', methods=['GET','POST'])
@login_required
def accept(id, aid):
    """
    Confirmation of acceptance of the answer.

    Could do as a popup after clicking button. Maybe. I dunno. Is there a way to pass Python scripting variables to
    JS? If so, this would just be a POST. No GET. Popup with HTML "url_for" etc etc. Would that work with JQUERY?
    :param id:
    :param aid:
    :return:
    """
    #TODO ensure only creator can do this. This is the confirmation. Maybe have JS. Also do Stripe Stuff.
    q = Question.query.get_or_404(id)
    a = Answer.query.get_or_404(aid)
    form = AcceptAnswerForm()
    if current_user == q.creator and form.validate_on_submit() and current_user.can(Permission.CREATE):
        a.accept()
        # TODO: Stripe transfer stuff and email to both asker and answerer
        flash("The answer has been accepted")
        return redirect(url_for("main.question", id=id))  # for now, redirect just to the original
    elif current_user == q.creator:
        return render_template('accept.html', q=q, a=a, form=form)
    else:
        flash("You're not the creator of this question")
        redirect(url_for(".question", id=id))



@main.route('/questions/<int:id>/report/', methods=['GET','POST'])
@login_required
def report(id):
    """
    Have a picture of a yeti or something on the side
    Why are X people terrible?
    :param id:
    :return:
    """
    form = ReportForm()
    if form.validate_on_submit():
        title = form.title.data
        complaint = form.complaint.data
        id = id
        try:
            send_grid_email(current_app.config['TIP_MAIL_ADDRESS'],"Pot Reported",'main_emails/pot_report', title=title,
                        complaint=complaint, id=id, user=current_user._get_current_object())
        except Exception as e:
            print(e) #TODO make errors do logging and also send full stack trace, this isn't right
        flash("Your annoyances have been ignored by the administration, please hold.")
    return render_template('report.html', id=id)


@main.route('/questions/<int:id>/toggle_question_visibility/', methods=['POST'])
@admin_required
@login_required
def toggle_visibility(id):
    q = Question.query.get_or_404(id)
    q.toggle_visibility()
    return redirect(url_for('main.question', id = id))


@main.route('/questions/')
def questions():
    """
    Displays all questions
    :return:
    """
    top = Question.query.filter_by(solved=False).limit(10).all() # Top pots by value
    questions = Question.query.filter_by(solved=False).order_by(Question.date.desc()).all()
    return render_template('questions.html', questions=questions, top=top)


@main.route('/categories/')
def categories():
    """
    categories view, lists all categories

    should remove this view and only allow links to
    :return:
    """
    # app = current_app._get_current_object()
    categories = current_app.config['CATEGORIES']
    return render_template('categories.html', categories=categories)


@main.route('/categories/<category>/')
def category(category):
    """
    View of a specific category, shows top 3 in the category then shows all
    http://harishvc.com/2015/04/15/pagination-flask-mongodb/
    http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ix-pagination
    NOTE: Don't forget to import _macros at top of categories.html
    :param category:
    :return:
    """
    q_ct = current_app.config['Q_PER_PAGE']
    if category == "top":
        matched = Question.query.filter_by(solved=False).order_by(Question.current_value.desc())#.limit(12).all()
    else:
        matched = Question.query.filter_by(solved=False,category=category).filter_by(solved=False)#.limit(12).all()
    if matched.count() > q_ct:
        page = request.args.get('page',1, type=int)
        pagination = matched.paginate(
            page,
            per_page=q_ct,
            error_out=False)
        matched = pagination.items
    else:
        pagination=None
    return render_template('category.html',endpoint='main.category', category=category, qs=matched, pagination=pagination)

@main.route('/about/')
def about():
    """
    show some statistics stuff, 
    :return:
    """
    questions = Question.query.count()
    return render_template('about.html', qs=questions)


@main.route('/contact/')
def contact():
    """
    Show contact deets
    :return:
    """
    # return render_template('contact.html')
    return redirect(url_for('main.index'))


@main.route('/jq_play/')
def jq_play():
    return render_template("jq_play.html")


@main.route('/_test_jq/', methods=['POST'])  # _in front for AJAX/JSON?
def test_jq():
    # since it is a POST, we access items as if data entered in HTML form
    # http://code.runnable.com/UiPhLHanceFYAAAP/how-to-perform-ajax-in-flask-for-python
    # http://stackoverflow.com/questions/21791037/implement-a-like-this-button-in-django-without-refreshing-page?rq=1
    # http://stackoverflow.com/questions/17072437/use-django-view-without-redirecting-or-refreshing-a-page
    # http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-ajax
    # Jquery or Angular
    # http://learn.jquery.com/ajax/
    print('test ', request.form['a'])
    return jsonify({'tested':True})